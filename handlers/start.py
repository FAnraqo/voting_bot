import random
import string
import os
from captcha.image import ImageCaptcha
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters
)
from utils.db import load_users, save_users

# Для временного хранения ожидающих капчу пользователей
pending_captcha: dict[int, str] = {}

# Генерация изображения капчи и отправка пользователю
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    pending_captcha[user_id] = text

    img = ImageCaptcha(width=200, height=70)
    file_path = f"/tmp/captcha_{user_id}.png"
    img.write(text, file_path)

    with open(file_path, 'rb') as f:
        await update.message.reply_photo(f, caption="🛡 Введите текст с картинки:")
    os.remove(file_path)

async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    answer = update.message.text.strip().upper()

    expected = pending_captcha.get(user_id)
    if expected is None:
        return  # или можно подсказать пользователю пройти /start

    if answer == expected:
        users = load_users()
        users.setdefault(str(user_id), {})["verified"] = True
        save_users(users)
        pending_captcha.pop(user_id, None)

        await update.message.reply_text(
            "✅ Капча пройдена!",
            reply_markup=ReplyKeyboardMarkup(
                [["📷 Перейти к голосованию"]],
                resize_keyboard=True,
                one_time_keyboard=True
            )
        )
    else:
        await update.message.reply_text(
            "❌ Неверно. Попробуйте ещё раз или введите /start для новой капчи."
        )

def register_handlers(app: ApplicationBuilder):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, verify))

if __name__ == "__main__":
    app = ApplicationBuilder().token("YOUR_TOKEN_HERE").build()
    register_handlers(app)
    app.run_polling()
