"""Общие клавиатуры для бота."""

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def main_keyboard() -> ReplyKeyboardMarkup:
    """Создаёт простую клавиатуру с основными командами.

    Кнопки отправляют команды в чат, чтобы новичку было проще пользоваться ботом.
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="/add"), KeyboardButton(text="/list")],
            [KeyboardButton(text="/list_csv")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите команду или введите /add текст задачи",
    )
