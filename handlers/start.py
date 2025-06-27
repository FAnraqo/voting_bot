from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, CommandHandler
from utils.db import load_users, save_users


def register_handlers(app):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_captcha, pattern="^captcha_pass$"))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Я не бот 🤖", callback_data='captcha_pass')]]
    await update.message.reply_text("Пройди капчу:", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_captcha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    users = load_users()

    if str(user_id) not in users:
        users[str(user_id)] = {"verified": True}
        save_users(users)

    await query.message.reply_text(
        "✅ Капча пройдена! Вы можете перейти к оценке фотографий.",
        reply_markup=ReplyKeyboardMarkup(
            [["📷 Перейти к голосованию"]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    )
