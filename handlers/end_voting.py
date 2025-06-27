from telegram.ext import ContextTypes
from utils.db import load_photos, all_user_ids
from telegram import Message

def register_handlers(app):
    pass  # не требует хендлеров

async def notify_results(context: ContextTypes.DEFAULT_TYPE):
    photos = load_photos()
    result_text = "🏁 Результаты фотоконкурса:\n\n"

    for category in ['nature', 'engineers', 'sports', 'other']:
        cat_photos = [p for p in photos.values() if p["category"] == category]
        if not cat_photos:
            continue
        winner = max(cat_photos, key=lambda x: x["votes"], default=None)
        if winner:
            result_text += f"🏆 {category.capitalize()}: {winner['author']} ({winner['votes']} голосов)\n"

    for user_id in all_user_ids():
        try:
            await context.bot.send_message(chat_id=int(user_id), text=result_text)
        except Exception:
            continue
