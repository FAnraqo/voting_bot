import random
import string
import os
from PIL import Image, ImageDraw, ImageFont
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from utils.db import load_users, save_users

# Словарь для хранения капчи в памяти (можно заменить на БД)
captcha_storage = {}

def register_handlers(app):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, verify_captcha))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Генерируем случайный текст капчи
    captcha_text = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    captcha_storage[user_id] = captcha_text

    # Создаем изображение
    image = Image.new('RGB', (200, 70), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)

    # Попробуем найти шрифт, или использовать дефолтный
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    if not os.path.exists(font_path):
        font = ImageFont.load_default()
    else:
        font = ImageFont.truetype(font_path, 40)

    draw.text((10, 10), captcha_text, font=font, fill=(0, 0, 0))

    # Сохраняем во временный файл
    file_path = f"/tmp/captcha_{user_id}.png"
    image.save(file_path)

    # Отправляем картинку пользователю
    await update.message.reply_photo(
        photo=open(file_path, 'rb'),
        caption="🛡 Введите текст с картинки для подтверждения, что вы не бот:"
    )

    # Удаляем файл после отправки (необязательно)
    os.remove(file_path)

async def verify_captcha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_input = update.message.text.strip()

    captcha_text = captcha_storage.get(user_id)

    if captcha_text and user_input.upper() == captcha_text:
        # Успех: сохраняем пользователя как проверенного
        users = load_users()
        if str(user_id) not in users:
            users[str(user_id)] = {"verified": True}
            save_users(users)

        # Убираем из памяти капчу
        captcha_storage.pop(user_id)

        await update.message.reply_text(
            "✅ Капча пройдена! Вы можете перейти к оценке фотографий.",
            reply_markup=ReplyKeyboardMarkup(
                [["📷 Перейти к голосованию"]],
                resize_keyboard=True,
                one_time_keyboard=True
            )
        )
    else:
        await update.message.reply_text(
            "❌ Неверный текст. Попробуйте снова, введя правильный текст с картинки или напишите /start для новой капчи."
        )
