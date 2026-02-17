import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config_data import config
from database.db import db
from database.models import Word  
from services.word_importer import import_all_decks
from services.notification import setup_notifications
from handlers import start_info, main_menu, learn_words, settings


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

async def main():

    db.create_tables()
    logger.info("База данных инициализирована")
    

    session = db.get_session()
    try:
        word_count_before = session.query(Word).count()
        logger.info("Слов в базе (до импорта): %d", word_count_before)
    finally:
        session.close()
    

    try:
        total_imported = import_all_decks()
        logger.info("Импорт колод завершён. Новых слов добавлено: %d", total_imported)
        

        session = db.get_session()
        try:
            word_count_after = session.query(Word).count()
            logger.info(f"Слов в базе после импорта: {word_count_after}")
            

            from sqlalchemy import func
            decks = session.query(Word.deck, func.count(Word.id)).group_by(Word.deck).all()
            for deck, count in decks:
                logger.info("Колода '%s': %d слов", deck, count)
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"Ошибка при импорте колод: {e}")
    

    token=config.BOT_TOKEN
    assert token, "BOT_TOKEN не задан в окружении"
    bot = Bot(token=token)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    

    dp.include_router(start_info.router)
    dp.include_router(main_menu.router)
    dp.include_router(learn_words.router)
    dp.include_router(settings.router)
    

    setup_notifications(bot)
    

    logger.info("Бот запущен")
    try:
        await dp.start_polling(bot)
    finally:
        from services.notification import notification_service
        if notification_service:
            notification_service.shutdown_scheduler()
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен")