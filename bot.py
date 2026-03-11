# bot.py
import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

# Добавляем FastAPI и uvicorn
from fastapi import FastAPI
import uvicorn

from database.engine import init_db
from handlers import register_handlers
from config import BOT_TOKEN  # или откуда берёшь токен

load_dotenv()

if not BOT_TOKEN:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN не найден!")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
register_handlers(dp)

# ── Минимальный HTTP-сервер для Render health check ──
app = FastAPI()

@app.get("/health")
@app.get("/")
async def health_check():
    return {"status": "alive", "bot": "running"}

# ── Запуск ──
async def on_startup():
    await init_db()
    print("База данных инициализирована и готова к работе")

async def on_shutdown():
    await bot.session.close()
    print("Бот остановлен, сессия закрыта")

async def main():
    await on_startup()

    # Запуск HTTP-сервера в фоне (Render требует 0.0.0.0 + PORT из env)
    port = int(os.getenv("PORT", 10000))  # Render сам подставит PORT
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=port,
        log_level="error",          # меньше спама в логах
        loop="asyncio"              # совместимо с aiogram
    )
    server = uvicorn.Server(config)
    asyncio.create_task(server.serve())  # запускаем в фоне

    print(f"HTTP health check запущен на порту {port}")

    try:
        print("Бот запущен и начал polling...")
        await dp.start_polling(bot, allowed_updates=["message", "callback_query"])
    except Exception as e:
        logging.error(f"Критическая ошибка в polling: {e}")
    finally:
        await on_shutdown()

if __name__ == "__main__":
    asyncio.run(main())
