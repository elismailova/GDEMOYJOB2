"""Точка входа: инициализация бота, регистрация роутеров и запуск polling."""
import os
# Модель уже в кэше — запрещаем обращение к HuggingFace при каждом запуске
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import config
from database import init_db
from bot.handlers import main_router
from bot.middlewares import DbSessionMiddleware
from nlp.matcher import get_embedding_model

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


async def on_startup(bot: Bot) -> None:
    logger.info("Инициализация БД...")
    await init_db()
    logger.info("Загрузка NLP-модели (первый запуск — несколько минут)...")
    await asyncio.get_event_loop().run_in_executor(None, get_embedding_model)
    logger.info("Бот запущен.")


async def main() -> None:
    if not config.BOT_TOKEN:
        logger.error("BOT_TOKEN не задан. Создайте файл .env на основе .env.example")
        sys.exit(1)

    bot = Bot(token=config.BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Middleware применяется ко всем update-событиям
    dp.update.middleware(DbSessionMiddleware())

    dp.include_router(main_router)
    dp.startup.register(on_startup)

    logger.info("Запуск polling...")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
