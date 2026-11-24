"""Обработчики команд для работы с задачами: /add, /cancel, /list, /list_csv."""

import csv
import io

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import BufferedInputFile, Message

from db import add_task, get_all_tasks

# Отдельный роутер для задач.
router = Router()

# Лимит Telegram на длину текстового сообщения — 4096 символов.
# Оставляем небольшой запас.
MAX_MESSAGE_LENGTH = 4000


class AddTask(StatesGroup):
    """Состояние ожидания текста новой задачи."""

    waiting_for_text = State()


def get_user_name(message: Message) -> str:
    """Возвращает имя пользователя, добавившего задачу."""
    default = "Неизвестный пользователь"
    if message.from_user:
        return message.from_user.full_name or message.from_user.username or default
    return default


def format_task(task: tuple[int, str, str, str]) -> str:
    """Преобразует задачу из базы в удобную строку для сообщения."""
    task_id, text, user, created_at = task
    return f"#{task_id} | {created_at}\nАвтор: {user}\nЗадача: {text}"


def split_task_list(tasks: list[tuple[int, str, str, str]]) -> list[str]:
    """Разбивает список задач на сообщения, не превышающие лимит Telegram."""
    chunks: list[str] = []
    current = "Список задач:\n\n"
    has_tasks = False

    for task in tasks:
        block = f"{format_task(task)}\n\n"
        if has_tasks and len(current) + len(block) > MAX_MESSAGE_LENGTH:
            chunks.append(current.strip())
            current = "Список задач (продолжение):\n\n"
            has_tasks = False
        current += block
        has_tasks = True

    if has_tasks:
        chunks.append(current.strip())

    return chunks


# ВАЖНО: обработчики команд регистрируются ДО обработчика состояния ввода.
# Иначе в режиме ожидания текста команды /list и /list_csv попадали бы
# в process_task_text и не выполнялись.


@router.message(Command("add"))
async def cmd_add(
    message: Message, command: CommandObject, state: FSMContext
) -> None:
    """Добавляет задачу в базу данных.

    Пример использования: /add Купить молоко
    Если текст не указан, бот ждёт следующее сообщение с текстом задачи.
    """
    # command.args содержит текст после команды.
    task_text = (command.args or "").strip()

    if task_text:
        task_id = add_task(task_text, get_user_name(message))
        await state.clear()
        await message.answer(f"Задача #{task_id} добавлена!")
        return

    # Кнопка /add отправляет команду без аргументов — ждём текст отдельным
    # сообщением и сохраняем его в состоянии пользователя.
    await state.set_state(AddTask.waiting_for_text)
    await message.answer("Введите текст задачи. Для отмены: /cancel")


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    """Отменяет ожидание текста задачи."""
    if await state.get_state() is None:
        await message.answer("Нет незавершённого добавления задачи.")
        return

    await state.clear()
    await message.answer("Добавление задачи отменено.")


@router.message(Command("list"))
async def cmd_list(message: Message) -> None:
    """Показывает все задачи из базы данных."""
    tasks = get_all_tasks()

    if not tasks:
        await message.answer("Список задач пока пуст. Добавьте первую: /add Текст задачи")
        return

    # Если задач много, отправляем несколько сообщений — одно сообщение
    # может превысить лимит Telegram, и тогда список не выведется вообще.
    for chunk in split_task_list(tasks):
        await message.answer(chunk)


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


# Обработчики состояния идут последними: они перехватывают произвольный текст,
# поэтому команды должны быть обработаны раньше.


@router.message(AddTask.waiting_for_text, F.text)
async def process_task_text(message: Message, state: FSMContext) -> None:
    """Сохраняет текст, введённый после команды /add."""
    task_text = (message.text or "").strip()

    # На всякий случай не сохраняем команды как текст задачи.
    if not task_text or task_text.startswith("/"):
        await message.answer(
            "Введите именно текст задачи (не команду) или /cancel для отмены."
        )
        return

    task_id = add_task(task_text, get_user_name(message))
    await state.clear()
    await message.answer(f"Задача #{task_id} добавлена!")


@router.message(AddTask.waiting_for_text)
async def process_non_text(message: Message) -> None:
    """Напоминает, что задача должна быть текстовым сообщением."""
    await message.answer("Нужно текстовое сообщение. Введите текст задачи или /cancel.")
