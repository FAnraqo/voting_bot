from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InputMediaPhoto, ReplyKeyboardMarkup, InputMediaPhoto
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from utils.db import load_photos, load_users, save_users, save_photos, load_votes, save_votes
import os
import json

CATEGORIES = ['nature', 'engineers', 'sports', 'other']

VOTES_FILE = "data/votes.json"
PHOTOS_FILE = "data/photos.json"

def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def register_handlers(app):
    app.add_handler(CommandHandler("vote", choose_category))
    app.add_handler(CallbackQueryHandler(handle_category, pattern="^cat_"))
    app.add_handler(CallbackQueryHandler(handle_vote, pattern="^vote_"))

async def choose_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    voted_categories = context.user_data.get("voted_categories", [])
    keyboard = []
    for c in CATEGORIES:
        if c not in voted_categories:
            keyboard.append([InlineKeyboardButton(c.capitalize(), callback_data=f"cat_{c}")])

    if not keyboard:
        await update.message.reply_text("Вы уже проголосовали во всех категориях!\nСледите за рейтингом фотографий.")
        return

    await update.message.reply_text("Выберите категорию:", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    category = update.callback_query.data.split("_")[1]

    photos = load_photos()

    if category not in photos or not photos[category]:
        await update.callback_query.message.reply_text("В этой категории нет фотографий.")
        return

    context.user_data["voting_category"] = category
    context.user_data["photo_ids"] = list(photos[category].keys())

    for photo_id, (path, author) in photos[category].items():
        try:
            with open(path, "rb") as f:
                button = InlineKeyboardMarkup([
                    [InlineKeyboardButton("Выбрать", callback_data=f"vote_{category}_{photo_id}")]
                ])
                await update.effective_chat.send_photo(f, caption=f"АВТОР: {author}", reply_markup=button)
        except Exception as e:
            print(f"Ошибка при открытии файла {path}: {e}")

async def handle_vote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        _, category, photo_id = query.data.split("_")
    except Exception:
        await query.edit_message_text("Неверный формат данных голосования.")
        return

    user_id = str(query.from_user.id)

    photos = load_photos()
    votes = load_votes()

    if category not in photos or photo_id not in photos[category]:
        await query.edit_message_text("Фотография не найдена.")
        return

    if category not in votes:
        votes[category] = {}

    if photo_id not in votes[category]:
        votes[category][photo_id] = {"votes": 0, "users": []}

    if user_id in votes[category][photo_id]["users"]:
        await query.edit_message_text("Вы уже голосовали за это фото.")
        return

    # Голосуем
    votes[category][photo_id]["votes"] += 1
    votes[category][photo_id]["users"].append(user_id)
    save_votes(votes)

    # Отмечаем категорию как пройденную
    voted_categories = context.user_data.get("voted_categories", [])
    if category not in voted_categories:
        voted_categories.append(category)
        context.user_data["voted_categories"] = voted_categories

    await query.edit_message_text("Спасибо! Ваш голос учтён.")

    # Предложить выбрать новую категорию
    if set(voted_categories) == set(CATEGORIES):
        await query.message.reply_text("Вы уже проголосовали во всех категориях.")
    else:
        keyboard = [
            [InlineKeyboardButton("Выбрать другую категорию", callback_data="cat_menu")],
            [InlineKeyboardButton("Закончить голосование", callback_data="end_vote")]
        ]
        await query.message.reply_text(
            "Хотите продолжить голосование в другой категории?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def enter_voting(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    # Можно проверить, прошёл ли пользователь капчу
    # if not is_verified(user_id): return

    await update.message.reply_text(
        "Выберите категорию для оценки:",
        reply_markup=ReplyKeyboardMarkup(
            [["🌿 Природа", "⚙️ Инженеры"], ["🏅 Спорт", "📁 Разное"]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    )

# Функция для загрузки путей к фото из папки категории
def get_photos_by_category(category: str):
    folder = os.path.join("media", category)
    photos = []
    if os.path.exists(folder):
        for file in os.listdir(folder):
            if file.lower().endswith((".jpg", ".jpeg", ".png")):
                photos.append(os.path.join(folder, file))
    return photos

async def handle_category_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    category_map = {
        "🌿 Природа": "природа",
        "⚙️ Инженеры": "инженеры",
        "🏅 Спорт": "спорт",
        "📁 Разное": "разное"
    }

    category_text = update.message.text.strip()
    if category_text not in category_map:
        await update.message.reply_text("Пожалуйста, выберите категорию из списка.")
        return

    category = category_map[category_text]
    context.user_data["voting_stage"] = 1
    context.user_data["voting_category"] = category
    context.user_data["first_round_choice"] = None
    context.user_data["second_round_choice"] = None

    photos = load_photos()

    if category not in photos:
        await update.message.reply_text("В этой категории нет фотографий.")
        return

    context.user_data["all_photos"] = list(photos[category].items())

    await send_photo_block(update, context, block_number=1)

async def send_photo_block(update, context, block_number):
    photos = context.user_data["all_photos"]
    total = len(photos)

    start = (block_number - 1) * 10
    end = min(start + 10, total)

    if start >= total:
        if update.callback_query and update.callback_query.message:
            await update.callback_query.message.reply_text("Нет больше фото.")
        elif update.message:
            await update.message.reply_text("Нет больше фото.")
        return

    media = []
    authors_text_lines = []
    for i in range(start, end):
        photo_path, author = photos[i][1]
        try:
            media.append(InputMediaPhoto(open(photo_path, "rb"), caption=f"АВТОР: {author}"))
            authors_text_lines.append(f"Фото {i - start + 1}: Автор — {author}")
        except Exception as e:
            print(f"Ошибка при открытии {photo_path}: {e}")

    if media:
        if update.callback_query and update.callback_query.message:
            await update.callback_query.message.reply_media_group(media)
            await update.callback_query.message.reply_text("\n".join(authors_text_lines))
        elif update.message:
            await update.message.reply_media_group(media)
            await update.message.reply_text("\n".join(authors_text_lines))
        else:
            print("Нет подходящего объекта для отправки медиа.")

    # Кнопки с нумерацией от 1 до 10 внутри блока и callback_data с глобальным индексом
    buttons = [
        [InlineKeyboardButton(f"Фото {j+1}", callback_data=f"choose_{block_number}_{i}")]
        for j, i in enumerate(range(start, end))
    ]
    markup = InlineKeyboardMarkup(buttons)

    if update.callback_query and update.callback_query.message:
        await update.callback_query.message.reply_text("Выберите фото:", reply_markup=markup)
    elif update.message:
        await update.message.reply_text("Выберите фото:", reply_markup=markup)

async def handle_vote_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data  # choose_1_3 (блок 1, фото 3)
    _, block_str, index_str = data.split("_")
    block = int(block_str)
    index = int(index_str)

    photos = context.user_data.get("all_photos", [])
    if index >= len(photos):
        await query.edit_message_text("Неверный выбор.")
        return

    chosen = photos[index]

    if block == 1:
        context.user_data["first_round_choice"] = chosen
        total_photos = len(photos)
        if total_photos > 10:
            await query.edit_message_text("Спасибо! Переходим ко второму блоку.")
            await send_photo_block(update, context, block_number=2)
        else:
            context.user_data["second_round_choice"] = None
            await send_final_choice(update, context)

    elif block == 2:
        context.user_data["second_round_choice"] = chosen
        await query.edit_message_text("Спасибо! Теперь выберите лучшее из двух фото.")
        await send_final_choice(update, context)

    elif block == 3:
        # Финальный выбор
        user_id = query.from_user.id
        category = context.user_data.get("voting_category")

        votes = load_json(VOTES_FILE)  # Или load_votes(), если есть своя функция
        if category not in votes:
            votes[category] = {}

        photo_id = str(index)
        if photo_id not in votes[category]:
            votes[category][photo_id] = {"votes": 0, "users": []}

        if user_id not in votes[category][photo_id]["users"]:
            votes[category][photo_id]["votes"] += 1
            votes[category][photo_id]["users"].append(user_id)
            save_json(VOTES_FILE, votes)

        # Обновляем список проголосованных категорий в user_data
        voted_categories = context.user_data.get("voted_categories", [])
        if category and category not in voted_categories:
            voted_categories.append(category)
            context.user_data["voted_categories"] = voted_categories

        # Проверяем, проголосовал ли пользователь во всех категориях
        if set(voted_categories) == set(CATEGORIES):
            await query.edit_message_text(
                "Спасибо! Вы проголосовали во всех категориях.\n"
                "Следите за рейтингом фотографий."
            )
        else:
            # Предлагаем продолжить голосовать
            keyboard = [
                [InlineKeyboardButton("Выбрать другую категорию", callback_data="cat_menu")],
                [InlineKeyboardButton("Закончить голосование", callback_data="end_vote")]
            ]
            markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "Спасибо за ваш выбор! Хотите продолжить голосовать в других категориях?",
                reply_markup=markup
            )

async def send_final_choice(update, context):
    chosen = []
    for key in ["first_round_choice", "second_round_choice"]:
        if context.user_data.get(key):
            chosen.append(context.user_data[key])

    media = []
    for idx, (photo_id, (path, author)) in enumerate(chosen):
        try:
            media.append(InputMediaPhoto(open(path, "rb"), caption=f"АВТОР: {author}"))
        except Exception as e:
            print(f"Ошибка при открытии {path}: {e}")

    if media:
        await update.effective_chat.send_media_group(media)

    buttons = [
        [InlineKeyboardButton(f"Фото {i+1}", callback_data=f"choose_3_{context.user_data['all_photos'].index(chosen[i])}")]
        for i in range(len(chosen))
    ]
    markup = InlineKeyboardMarkup(buttons)

    await update.effective_chat.send_message("Выберите лучшее из выбранных ранее фото:", reply_markup=markup)

async def handle_continue_vote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "cat_menu":
        voted_categories = context.user_data.get("voted_categories", [])
        keyboard = []
        for c in CATEGORIES:
            if c not in voted_categories:
                keyboard.append([InlineKeyboardButton(c.capitalize(), callback_data=f"cat_{c}")])

        if not keyboard:
            await query.edit_message_text("Вы уже проголосовали во всех категориях!\nСледите за рейтингом фотографий.")
            return

        await query.edit_message_text("Выберите категорию:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "end_vote":
        await query.edit_message_text("Спасибо за участие! Вы всегда можете вернуться и проголосовать снова.")
