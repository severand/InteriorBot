
# import asyncio
# import logging
# from aiogram import Bot, Dispatcher
# from aiogram.client.default import DefaultBotProperties
# from aiogram.enums import ParseMode
#
# # Импорты конфигурации (на уровне проекта)
# from config import config
# from config import ADMIN_IDS
# from database.db import Database  # Изменил с db на Database для явного импорта
# from handlers import user_start, creation, payment
# from services.replicate_api import generate_image  # Убеждаемся, что импорт работает
#
# # Configure logging
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# )
# logger = logging.getLogger(__name__)
#
# # Инициализируем базу данных (теперь это класс, а не объект)
# db = Database(db_path=config.DB_PATH)  # Используем класс Database из db.py
#
# # Initialize bot
# bot = Bot(
#     token=config.BOT_TOKEN,
#     default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
# )
#
#
# async def main():
#     """Main bot function"""
#     # Initialize database
#     await db.init_db()
#     logger.info("Database initialized")
#
#     # Initialize dispatcher
#     dp = Dispatcher()
#
#     # Register routers
#     dp.include_routers(
#         user_start.router,
#         creation.router,
#         payment.router,
#     )
#
#     # Передаем ADMIN_IDS и BOT_TOKEN в контекст для использования в хэндлерах
#     dp["admins"] = ADMIN_IDS
#     dp["bot_token"] = config.BOT_TOKEN  # <-- ДОБАВЛЕНО
#
#     logger.info("Bot started")
#
#     try:
#         # Start polling
#         logger.info(f"Run polling for bot @{bot.default.username} id={bot.id} - '{bot.default.username}'")
#         await dp.start_polling(bot)
#     finally:
#         await bot.session.close()
#
#
# if __name__ == "__main__":
#     try:
#         asyncio.run(main())
#     except KeyboardInterrupt:
#         logger.info("Bot stopped by user")



import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

# Импорты конфигурации (на уровне проекта)
from config import config
from config import ADMIN_IDS
from database.db import Database  # Изменил с db на Database для явного импорта
from handlers import user_start, creation, payment
from services.replicate_api import generate_image  # Убеждаемся, что импорт работает

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализируем базу данных (теперь это класс, а не объект)
db = Database(db_path=config.DB_PATH)  # Используем класс Database из db.py

# Initialize bot
bot = Bot(
    token=config.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
)


async def main():
    """Main bot function"""
    # Initialize database
    await db.init_db()
    logger.info("Database initialized")

    # Initialize dispatcher
    dp = Dispatcher()

    # Register routers
    dp.include_routers(
        user_start.router,
        creation.router,
        payment.router,
    )

    # Передаем ADMIN_IDS и BOT_TOKEN в контекст для использования в хэндлерах
    dp["admins"] = ADMIN_IDS
    dp["bot_token"] = config.BOT_TOKEN  # <-- ДОБАВЛЕНО

    logger.info("Bot started")

    try:
        # Get bot info
        me = await bot.get_me()
        logger.info(f"Run polling for bot @{me.username} id={me.id} - '{me.username}'")

        # Start polling
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
