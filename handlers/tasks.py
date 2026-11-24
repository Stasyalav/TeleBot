"""Обработчики команд для работы с задачами.

Команды: /add, /edit, /cancel, /list, /list_csv.
Полная история правок показывается прямо в выводе /list и /list_csv.
"""

import csv
import io

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db import (
    TaskRow,
    add_task,
    get_all_tasks,
    get_task,
    parse_history,
    update_task,
)

# Отдельный роутер для задач.
router = Router()

# Лимит Telegram на длину текстового сообщения — 4096 символов.
# Оставляем небольшой запас.
MAX_MESSAGE_LENGTH = 4000

# Сколько задач показывать на одной странице списка для редактирования.
EDIT_PAGE_SIZE = 8


class AddTask(StatesGroup):
    """Состояние ожидания текста новой задачи."""

    waiting_for_text = State()


class EditTask(StatesGroup):
    """Состояние ожидания нового текста существующей задачи."""

    waiting_for_new_text = State()


def get_user_name(message: Message) -> str:
    """Возвращает имя пользователя, добавившего или изменившего задачу."""
    default = "Неизвестный пользователь"
    if message.from_user:
        return message.from_user.full_name or message.from_user.username or default
    return default


def format_task(task: TaskRow) -> str:
    """Преобразует задачу в сообщение, включая полную историю правок."""
    task_id, text, user, created_at, updated_at, updated_by, raw_history = task
    lines = [
        f"#{task_id} | {created_at}",
        f"Автор: {user}",
        f"Задача: {text}",
    ]
    if updated_at:
        lines.append(f"Изменено: {updated_at} | {updated_by or 'Неизвестный пользователь'}")

    # История хранится в самой задаче, поэтому выводим её здесь же целиком.
    entries = parse_history(raw_history)
    if entries:
        lines.append("История изменений:")
        for number, entry in enumerate(entries, start=1):
            lines.append(
                f"  {number}. {entry.get('at', '?')} | {entry.get('by', '?')}: "
                f"«{entry.get('old', '')}» → «{entry.get('new', '')}»"
            )
    return "\n".join(lines)


def split_blocks(blocks: list[str], header: str) -> list[str]:
    """Разбивает блоки текста на сообщения, не превышающие лимит Telegram."""
    chunks: list[str] = []
    current = f"{header}:\n\n"
    has_blocks = False

    for block in blocks:
        if has_blocks and len(current) + len(block) > MAX_MESSAGE_LENGTH:
            chunks.append(current.strip())
            current = f"{header} (продолжение):\n\n"
            has_blocks = False
        current += block
        has_blocks = True

    if has_blocks:
        chunks.append(current.strip())

    return chunks


def split_task_list(tasks: list[TaskRow]) -> list[str]:
    """Разбивает список задач на сообщения, не превышающие лимит Telegram."""
    return split_blocks([f"{format_task(task)}\n\n" for task in tasks], "Список задач")


def build_edit_keyboard(tasks: list[TaskRow], page: int) -> InlineKeyboardMarkup:
    """Создаёт инлайн-клавиатуру со списком задач и кнопками навигации."""
    builder = InlineKeyboardBuilder()
    start = page * EDIT_PAGE_SIZE

    for task in tasks[start : start + EDIT_PAGE_SIZE]:
        builder.button(text=f"Изменить #{task[0]}", callback_data=f"edit:{task[0]}")
    builder.adjust(2)

    navigation: list[InlineKeyboardButton] = []
    if page > 0:
        navigation.append(
            InlineKeyboardButton(text="<< Назад", callback_data=f"edit_page:{page - 1}")
        )
    if start + EDIT_PAGE_SIZE < len(tasks):
        navigation.append(
            InlineKeyboardButton(text="Вперёд >>", callback_data=f"edit_page:{page + 1}")
        )
    if navigation:
        builder.row(*navigation)

    return builder.as_markup()


# ВАЖНО: обработчики команд и callback-запросов регистрируются ДО обработчиков
# состояний. Иначе команды и нажатия кнопок перехватывались бы как текст задачи.


@router.message(Command("add"))
async def cmd_add(
    message: Message, command: CommandObject, state: FSMContext
) -> None:
    """Добавляет задачу в базу данных.

    Пример использования: /add Купить молоко
    Если текст не указан, бот ждёт следующее сообщение с текстом задачи.
    """
    # Новое действие сбрасывает возможное незавершённое изменение задачи.
    await state.clear()

    # command.args содержит текст после команды.
    task_text = (command.args or "").strip()

    if task_text:
        task_id = add_task(task_text, get_user_name(message))
        await message.answer(f"Задача #{task_id} добавлена!")
        return

    # Кнопка /add отправляет команду без аргументов — ждём текст отдельным
    # сообщением и сохраняем его в состоянии пользователя.
    await state.set_state(AddTask.waiting_for_text)
    await message.answer("Введите текст задачи. Для отмены: /cancel")


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    """Отменяет незавершённый ввод или изменение задачи."""
    if await state.get_state() is None:
        await message.answer("Нет незавершённого ввода.")
        return

    await state.clear()
    await message.answer("Ввод отменён.")


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
    writer.writerow(
        ["id", "text", "user", "created_at", "updated_at", "updated_by", "history"]
    )

    # Данные задач.
    for task in tasks:
        writer.writerow(task)

    # Превращаем текст CSV в байты для отправки файлом.
    csv_bytes = output.getvalue().encode("utf-8-sig")
    file = BufferedInputFile(csv_bytes, filename="tasks.csv")

    await message.answer_document(file, caption="Вот список задач в формате CSV.")


@router.message(Command("edit"))
async def cmd_edit(message: Message, state: FSMContext) -> None:
    """Показывает список задач с кнопками для интерактивного изменения."""
    await state.clear()
    tasks = get_all_tasks()

    if not tasks:
        await message.answer("Список задач пока пуст. Добавьте первую: /add Текст задачи")
        return

    await message.answer(
        "Выберите задачу для изменения:",
        reply_markup=build_edit_keyboard(tasks, page=0),
    )


@router.callback_query(F.data.startswith("edit_page:"))
async def show_edit_page(callback: CallbackQuery) -> None:
    """Показывает следующую/предыдущую страницу списка задач для правки."""
    await callback.answer()

    try:
        page = int(callback.data.split(":", 1)[1])
    except (ValueError, AttributeError):
        return

    tasks = get_all_tasks()
    if not tasks:
        if isinstance(callback.message, Message):
            await callback.message.edit_text("Список задач пока пуст.")
        return

    max_page = max(0, (len(tasks) - 1) // EDIT_PAGE_SIZE)
    page = min(max(page, 0), max_page)
    keyboard = build_edit_keyboard(tasks, page)

    if isinstance(callback.message, Message):
        await callback.message.edit_reply_markup(reply_markup=keyboard)
    elif callback.message:
        await callback.bot.send_message(
            chat_id=callback.message.chat.id,
            text="Выберите задачу для изменения:",
            reply_markup=keyboard,
        )


@router.callback_query(F.data.startswith("edit:"))
async def start_task_edit(callback: CallbackQuery, state: FSMContext) -> None:
    """Начинает изменение выбранной задачи: запрашивает новый текст."""
    try:
        task_id = int(callback.data.split(":", 1)[1])
    except (ValueError, AttributeError):
        await callback.answer()
        return

    task = get_task(task_id)
    if task is None:
        await callback.answer("Задача не найдена", show_alert=True)
        return

    await callback.answer()
    await state.set_state(EditTask.waiting_for_new_text)
    await state.update_data(edit_task_id=task_id)

    # Показываем текущий текст, чтобы пользователю было проще редактировать.
    prompt = (
        f"Задача #{task_id}\nТекущий текст: {task[1]}\n\n"
        "Введите новый текст. Для отмены: /cancel"
    )
    if isinstance(callback.message, Message):
        await callback.message.answer(prompt)
    elif callback.message:
        await callback.bot.send_message(chat_id=callback.message.chat.id, text=prompt)


# Обработчики состояний идут последними: они перехватывают произвольный текст,
# поэтому команды и callback-запросы должны быть обработаны раньше.


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


@router.message(EditTask.waiting_for_new_text, F.text)
async def process_new_task_text(message: Message, state: FSMContext) -> None:
    """Сохраняет новый текст задачи с датой и автором изменения."""
    new_text = (message.text or "").strip()

    if not new_text or new_text.startswith("/"):
        await message.answer(
            "Введите именно новый текст задачи (не команду) или /cancel для отмены."
        )
        return

    data = await state.get_data()
    task_id = data.get("edit_task_id")

    if not isinstance(task_id, int):
        await state.clear()
        await message.answer("Не удалось определить задачу. Повторите /edit.")
        return

    # Изменять задачу может любой пользователь — проверка прав не требуется.
    if not update_task(task_id, new_text, get_user_name(message)):
        await state.clear()
        await message.answer(f"Задача #{task_id} не найдена.")
        return

    await state.clear()
    task = get_task(task_id)
    if task is None:
        await message.answer(f"Задача #{task_id} изменена!")
        return

    await message.answer(f"Задача #{task_id} изменена!\n\n{format_task(task)}")


@router.message(EditTask.waiting_for_new_text)
async def process_non_text_for_edit(message: Message) -> None:
    """Напоминает, что новый текст задачи должен быть сообщением."""
    await message.answer(
        "Нужно текстовое сообщение. Введите новый текст задачи или /cancel."
    )
