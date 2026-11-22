"""Обработчики команд для работы с задачами: /add, /list, /list_csv."""

import csv
import io

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import BufferedInputFile, Message

from db import add_task, get_all_tasks

# Отдельный роутер для задач.
router = Router()


def format_task(task: tuple[int, str, str, str]) -> str:
    """Преобразует задачу из базы в удобную строку для сообщения."""
    task_id, text, user, created_at = task
    return f"#{task_id} | {created_at}\nАвтор: {user}\nЗадача: {text}"


@router.message(Command("add"))
async def cmd_add(message: Message, command: CommandObject) -> None:
    """Добавляет задачу в базу данных.

    Пример использования: /add Купить молоко
    """
    # command.args содержит текст после команды.
    task_text = (command.args or "").strip()

    if not task_text:
        await message.answer(
            "Пожалуйста, укажите текст задачи.\n"
            "Пример: /add Купить молоко"
        )
        return

    # Определяем имя пользователя, который добавил задачу.
    user = "Неизвестный пользователь"
    if message.from_user:
        user = message.from_user.full_name or message.from_user.username or user

    task_id = add_task(task_text, user)
    await message.answer(f"Задача #{task_id} добавлена!")


@router.message(Command("list"))
async def cmd_list(message: Message) -> None:
    """Показывает все задачи из базы данных."""
    tasks = get_all_tasks()

    if not tasks:
        await message.answer("Список задач пока пуст. Добавьте первую: /add Текст задачи")
        return

    # Собираем все задачи в одно сообщение.
    lines = ["Список задач:\n"]
    for task in tasks:
        lines.append(format_task(task))
        lines.append("")  # Пустая строка между задачами.

    await message.answer("\n".join(lines).strip())


@router.message(Command("list_csv"))
async def cmd_list_csv(message: Message) -> None:
    """Отправляет CSV-файл со всеми задачами."""
    tasks = get_all_tasks()

    if not tasks:
        await message.answer("Список задач пока пуст. Добавьте первую: /add Текст задачи")
        return

    # Создаём CSV в памяти, чтобы не сохранять временный файл на диск.
    output = io.StringIO()
    writer = csv.writer(output)

    # Заголовки колонок.
    writer.writerow(["id", "text", "user", "created_at"])

    # Данные задач.
    for task in tasks:
        writer.writerow(task)

    # Превращаем текст CSV в байты для отправки файлом.
    csv_bytes = output.getvalue().encode("utf-8-sig")
    file = BufferedInputFile(csv_bytes, filename="tasks.csv")

    await message.answer_document(file, caption="Вот список задач в формате CSV.")
