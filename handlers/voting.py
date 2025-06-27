from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InputMediaPhoto, ReplyKeyboardMarkup, InputMediaPhoto
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from utils.db import load_photos, load_users, save_users, save_photos, load_votes, save_votes
import os

CATEGORIES = ['nature', 'engineers', 'sports', 'other']

def register_handlers(app):
    app.add_handler(CommandHandler("vote", choose_category))
    app.add_handler(CallbackQueryHandler(handle_category, pattern="^cat_"))
    app.add_handler(CallbackQueryHandler(handle_vote, pattern="^vote_"))

async def choose_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(c.capitalize(), callback_data=f"cat_{c}")] for c in CATEGORIES]
    await update.message.reply_text("Выберите категорию:", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    category = update.callback_query.data.split("_")[1]
    photos = load_photos()
    photo_list = [p for p in photos.values() if p["category"] == category]
    
    context.user_data["voting_category"] = category
    context.user_data["photo_ids"] = [p["id"] for p in photo_list]

    for p in photo_list:
        button = InlineKeyboardMarkup([[InlineKeyboardButton("Выбрать", callback_data=f"vote_{p['id']}")]])
        await update.effective_chat.send_photo(p["file_id"], caption=f"АВТОР: {p['author']}", reply_markup=button)

async def handle_vote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data  # формат: vote_природа_0
    try:
        _, category, photo_index = data.split("_")
        photo_index = int(photo_index)
    except Exception as e:
        await query.edit_message_text("Ошибка обработки выбора.")
        return

    user_id = query.from_user.id
    votes = load_votes()

    # Инициализация категории и фото, если нужно
    if category not in votes:
        votes[category] = {}

    if str(photo_index) not in votes[category]:
        votes[category][str(photo_index)] = {
            "votes": 0,
            "users": []
        }

    if user_id in votes[category][str(photo_index)]["users"]:
        await query.edit_message_text("Вы уже голосовали за это фото.")
        return

    # Регистрируем голос
    votes[category][str(photo_index)]["votes"] += 1
    votes[category][str(photo_index)]["users"].append(user_id)
    save_votes(votes)

    await query.edit_message_text("Спасибо! Ваш голос засчитан.")

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
    category = update.message.text.strip()

    valid_categories = ["🌿 Природа", "⚙️ Инженеры", "🏅 Спорт", "📁 Разное"]
    if category not in valid_categories:
        await update.message.reply_text("Пожалуйста, выберите категорию из кнопок.")
        return

    category_map = {
        "🌿 Природа": "природа",
        "⚙️ Инженеры": "инженеры",
        "🏅 Спорт": "спорт",
        "📁 Разное": "разное"
    }
    folder_name = category_map[category]

    photos = get_photos_by_category(folder_name)
    if not photos:
        await update.message.reply_text("В этой категории пока нет фотографий.")
        return

    # Отправим первые 3 фото
    media_group = []
    for photo_path in photos[:3]:
        media_group.append(InputMediaPhoto(open(photo_path, "rb")))

    await update.message.reply_media_group(media_group)

    # Создаем кнопки для выбора фото (по номерам)
    buttons = []
    for i in range(min(len(photos), 3)):
        buttons.append([InlineKeyboardButton(text=f"Фото {i+1}", callback_data=f"vote_{folder_name}_{i}")])

    reply_markup = InlineKeyboardMarkup(buttons)

    await update.message.reply_text(
        "Выберите фотографию для оценки, нажав на кнопку ниже:",
        reply_markup=reply_markup
    )
