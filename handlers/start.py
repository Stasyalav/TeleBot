"""Обработчик команды /start."""

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from keyboards import main_keyboard

# Router — это "маршрутизатор", который хранит обработчики сообщений.
router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Приветствует пользователя и показывает доступные команды."""
    text = (
        "Привет! Я бот для общего списка задач.\n\n"
        "Доступные команды:\n"
        "/add <текст задачи> — добавить задачу (или просто /add, затем ввести текст)\n"
        "/edit — изменить задачу (выберите её из списка)\n"
        "/cancel — отменить ввод или изменение\n"
        "/list — показать все задачи\n"
        "/list_csv — получить задачи в CSV-файле"
    )
    await message.answer(text, reply_markup=main_keyboard())
