from telegram.ext import Application, MessageHandler, filters, ApplicationBuilder, CommandHandler, CallbackQueryHandler
from config import TOKEN
from handlers import start, voting, rating
from handlers.voting import enter_voting, handle_category_choice, handle_vote, handle_vote_choice, handle_continue_vote
from handlers.rating import show_rating
from utils.scheduler import setup_scheduler

def main():
    app = Application.builder().token(TOKEN).post_init(setup_scheduler).build()

    # Регистрируем handlers
    start.register_handlers(app)
    voting.register_handlers(app)
    rating.register_handlers(app)
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("📷 Перейти к голосованию"), enter_voting))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^(🌿 Природа|⚙️ Инженеры|🏅 Спорт|📁 Разное)$"), handle_category_choice))
    app.add_handler(CallbackQueryHandler(handle_vote, pattern="^vote_"))
    app.add_handler(CommandHandler("rating", show_rating))
    app.add_handler(CallbackQueryHandler(handle_vote_choice, pattern="^choose_"))
    app.add_handler(CallbackQueryHandler(handle_continue_vote, pattern="^(cat_menu|end_vote)$"))

    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
