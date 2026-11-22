"""Точка входа в Telegram-бота."""

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession

from config import BOT_TOKEN
from db import init_db
from handlers import start_router, tasks_router


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    if not BOT_TOKEN:
        raise ValueError("Не задан BOT_TOKEN.")

    init_db()

    session = AiohttpSession(proxy="socks5://127.0.0.1:10808")
    bot = Bot(token=BOT_TOKEN, session=session)

    dp = Dispatcher()
    dp.include_router(start_router)
    dp.include_router(tasks_router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())