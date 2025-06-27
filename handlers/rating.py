from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes
from utils.db import load_photos
from config import VOTING_END_TIME
from datetime import datetime

def register_handlers(app):
    app.add_handler(CommandHandler("rating", rating_menu))
    app.add_handler(CallbackQueryHandler(show_rating, pattern="^rating_"))

async def rating_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(c.capitalize(), callback_data=f"rating_{c}")] for c in ['nature', 'engineers', 'sports', 'other']]
    await update.message.reply_text("Выберите категорию рейтинга:", reply_markup=InlineKeyboardMarkup(keyboard))

async def show_rating(update: Update, context: ContextTypes.DEFAULT_TYPE):
    category = update.callback_query.data.split("_")[1]
    photos = load_photos()
    cat_photos = [p for p in photos.values() if p["category"] == category]
    sorted_photos = sorted(cat_photos, key=lambda x: x["votes"], reverse=True)

    time_left = datetime.strptime(VOTING_END_TIME, "%Y-%m-%d %H:%M:%S") - datetime.now()
    text = f"🏆 Рейтинг: {category.capitalize()}\n⏳ До конца голосования: {time_left}\n\n"
    for p in sorted_photos:
        text += f"{p['author']} — {p['votes']} голосов\n"

    await update.callback_query.message.edit_text(text)
