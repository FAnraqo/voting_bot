from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes
from utils.db import load_photos, load_votes
from config import VOTING_END_TIME
from datetime import datetime

def register_handlers(app):
    app.add_handler(CommandHandler("rating", rating_menu))
    app.add_handler(CallbackQueryHandler(show_rating, pattern="^rating_"))

def get_rating_by_category(votes_dict, top_n=3):
    result = {}
    for category, photos in votes_dict.items():
        sorted_photos = sorted(
            photos.items(),
            key=lambda item: item[1]["votes"],
            reverse=True
        )
        result[category] = sorted_photos[:top_n]
    return result

async def rating_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(c.capitalize(), callback_data=f"rating_{c}")] for c in ['nature', 'engineers', 'sports', 'other']]
    await update.message.reply_text("Выберите категорию рейтинга:", reply_markup=InlineKeyboardMarkup(keyboard))

async def show_rating(update: Update, context: ContextTypes.DEFAULT_TYPE):
    votes = load_votes()
    rating = get_rating_by_category(votes)

    if not rating:
        await update.message.reply_text("Рейтинг пока пуст 😕")
        return

    message = "🏆 Топ фото по категориям:\n\n"
    for category, photos in rating.items():
        message += f"📂 {category}:\n"
        for i, (photo_id, data) in enumerate(photos, 1):
            message += f"  {i}. 🖼 Фото {photo_id}, 👍 Голосов: {data['votes']}\n"
        message += "\n"

    await update.message.reply_text(message.strip())