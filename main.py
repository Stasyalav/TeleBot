"""Точка входа в Telegram-бота."""

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from config import BOT_TOKEN, PROXY_URL
from db import init_db
from handlers import start_router, tasks_router

# Команды, которые Telegram показывает в фиксированном меню бота (меню "/").
BOT_COMMANDS = [
    BotCommand(command="start", description="Приветствие и список команд"),
    BotCommand(command="add", description="Добавить задачу"),
    BotCommand(command="edit", description="Изменить задачу"),
    BotCommand(command="list", description="Показать все задачи"),
    BotCommand(command="list_csv", description="Скачать задачи в CSV"),
    BotCommand(command="cancel", description="Отменить ввод или изменение"),
]


async def register_commands(bot: Bot) -> None:
    """Регистрирует команды бота в фиксированном меню Telegram."""
    await bot.set_my_commands(BOT_COMMANDS)


async def main() -> None:
    """Инициализирует БД, создаёт бота и запускает polling."""
    logging.basicConfig(level=logging.INFO)

    if not BOT_TOKEN:
        raise ValueError("Не задан BOT_TOKEN.")

    init_db()

    # Прокси необязателен: если PROXY_URL не задан, работаем напрямую.
    session = AiohttpSession(proxy=PROXY_URL) if PROXY_URL else AiohttpSession()
    bot = Bot(token=BOT_TOKEN, session=session)

    # Хранилище нужно для пошагового ввода задачи после команды /add.
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(start_router)
    dp.include_router(tasks_router)

    await bot.delete_webhook(drop_pending_updates=True)
    await register_commands(bot)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())