# bot.py

import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
import os

from config import BOT_TOKEN  # предполагаем, что BOT_TOKEN берётся из config.py или .env
from database.engine import init_db
from handlers import register_handlers

# Загружаем .env (если используешь)
load_dotenv()

# На всякий случай проверяем токен
if not BOT_TOKEN:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN не найден ни в config.py, ни в переменных окружения!")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Регистрируем все роутеры
register_handlers(dp)

async def on_startup():
    await init_db()
    print("База данных инициализирована и готова к работе")


async def on_shutdown():
    await bot.session.close()
    print("Бот остановлен, сессия закрыта")


async def main():
    await on_startup()
    try:
        print("Бот запущен и начал polling...")
        await dp.start_polling(bot, allowed_updates=["message", "callback_query"])
    except Exception as e:
        logging.error(f"Критическая ошибка в polling: {e}")
    finally:
        await on_shutdown()


if __name__ == "__main__":
    asyncio.run(main())