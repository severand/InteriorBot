# --- ИСПРАВЛЕНИЯ ВЕРСИИ: bot/main.py ---
# [2025-11-22 11:35 CET] Исправление: Уровень логирования изменен на DEBUG для детальной отладки срабатывания хэндлеров.
# [2025-12-03] Добавлен роутер referral для реферальной системы
# ----

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from config import ADMIN_IDS
# Импорты конфигурации (на уровне проекта)
from config import config
from database.db import Database
from handlers import user_start, creation, payment, referral

# Configure logging
logging.basicConfig(
    # ИЗМЕНЕНО: Понижаем уровень для детальной отладки
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализируем базу данных (теперь это класс, а не объект)
db = Database(db_path=config.DB_PATH)

# Initialize bot
bot = Bot(
    token=config.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
)


async def main():
    """Основная функция бота"""
    # Initialize database
    await db.init_db()
    logger.info("База данных инициализирована")

    # Initialize dispatcher
    dp = Dispatcher()

    # Register routers (Регистрируем роутеры)
    dp.include_routers(
        user_start.router,
        creation.router,
        payment.router,
        referral.router,  # НОВЫЙ роутер для реферальной системы
    )

    # Передаем ADMIN_IDS и BOT_TOKEN в контекст для использования в хэндлерах
    dp["admins"] = ADMIN_IDS
    dp["bot_token"] = config.BOT_TOKEN

    logger.info("Бот запущен")

    try:
        # Get bot info
        me = await bot.get_me()
        logger.info(f"Run polling for bot @{me.username} id={me.id} - '{me.first_name}'")

        # Start polling
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
