"""Функции для работы с SQLite3.

Здесь создаётся таблица tasks и выполняются основные операции:
- добавить задачу;
- получить список задач;
- изменить задачу с фиксацией автора, времени и полной истории правок.

История изменений хранится прямо в строке задачи, в колонке history
в формате JSON-массива: [{"old": ..., "new": ..., "at": ..., "by": ...}, ...].
"""

import json
import sqlite3
from datetime import datetime

from config import DB_PATH

# Формат даты/времени, единый для created_at и edited_at.
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Тип строки задачи:
# (id, text, user, created_at, updated_at, updated_by, history).
TaskRow = tuple[int, str, str, str, str | None, str | None, str]


def get_connection() -> sqlite3.Connection:
    """Создаёт подключение к базе данных SQLite."""
    # check_same_thread=False позволяет использовать соединение в разных местах,
    # но для простоты в этом примере мы открываем соединение на каждую операцию.
    return sqlite3.connect(DB_PATH)


def init_db() -> None:
    """Создаёт таблицу, если её нет, и мигрирует базу старых версий."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Для новой базы сразу создаём все колонки.
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                user TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT,
                updated_by TEXT,
                history TEXT NOT NULL DEFAULT '[]'
            )
            """
        )

        # Миграция: в старой БД некоторых колонок ещё нет.
        # CREATE TABLE IF NOT EXISTS не добавляет колонки, поэтому вызываем
        # ALTER TABLE только для отсутствующих полей.
        columns = {row[1] for row in cursor.execute("PRAGMA table_info(tasks)")}
        if "updated_at" not in columns:
            cursor.execute("ALTER TABLE tasks ADD COLUMN updated_at TEXT")
        if "updated_by" not in columns:
            cursor.execute("ALTER TABLE tasks ADD COLUMN updated_by TEXT")
        if "history" not in columns:
            cursor.execute(
                "ALTER TABLE tasks ADD COLUMN history TEXT NOT NULL DEFAULT '[]'"
            )

        # Миграция с предыдущей версии, где история лежала в отдельной таблице.
        # Переносим записи в колонку задачи, затем удаляем старую таблицу.
        tables = {
            row[0]
            for row in cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        if "task_edits" in tables:
            legacy = cursor.execute(
                """
                SELECT task_id, old_text, new_text, edited_at, editor
                FROM task_edits ORDER BY id ASC
                """
            ).fetchall()
            grouped: dict[int, list[dict[str, str]]] = {}
            for task_id, old_text, new_text, edited_at, editor in legacy:
                grouped.setdefault(task_id, []).append(
                    {
                        "old": old_text,
                        "new": new_text,
                        "at": edited_at,
                        "by": editor,
                    }
                )

            for task_id, entries in grouped.items():
                row = cursor.execute(
                    "SELECT history FROM tasks WHERE id = ?", (task_id,)
                ).fetchone()
                if row is None:
                    continue
                existing = parse_history(row[0])
                merged = existing + entries
                cursor.execute(
                    "UPDATE tasks SET history = ? WHERE id = ?",
                    (json.dumps(merged, ensure_ascii=False), task_id),
                )

            cursor.execute("DROP TABLE task_edits")

        conn.commit()


def parse_history(history: str | None) -> list[dict[str, str]]:
    """Безопасно разбирает JSON-историю задачи; при ошибке возвращает []."""
    if not history:
        return []
    try:
        entries = json.loads(history)
    except (ValueError, TypeError):
        return []
    if not isinstance(entries, list):
        return []
    return [entry for entry in entries if isinstance(entry, dict)]


def add_task(text: str, user: str) -> int:
    """Сохраняет новую задачу в базу и возвращает её ID."""
    created_at = datetime.now().strftime(DATE_FORMAT)

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO tasks (text, user, created_at, history)
            VALUES (?, ?, ?, '[]')
            """,
            (text, user, created_at),
        )
        conn.commit()
        # lastrowid содержит ID добавленной строки.
        return int(cursor.lastrowid)


def get_all_tasks() -> list[TaskRow]:
    """Возвращает все задачи из базы вместе с полной историей правок."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, text, user, created_at, updated_at, updated_by, history
            FROM tasks ORDER BY id ASC
            """
        )
        return cursor.fetchall()


def get_task(task_id: int) -> TaskRow | None:
    """Возвращает одну задачу по ID или None, если её нет."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, text, user, created_at, updated_at, updated_by, history
            FROM tasks WHERE id = ?
            """,
            (task_id,),
        )
        return cursor.fetchone()


def update_task(task_id: int, new_text: str, editor: str) -> bool:
    """Изменяет текст задачи и дописывает правку в её историю.

    Обновляет updated_at/updated_by и history, но оставляет created_at
    без изменений. Возвращает False, если задачи с таким ID не существует.
    """
    edited_at = datetime.now().strftime(DATE_FORMAT)

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT text, history FROM tasks WHERE id = ?
            """,
            (task_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return False
        old_text, raw_history = row

        entries = parse_history(raw_history)
        entries.append(
            {"old": old_text, "new": new_text, "at": edited_at, "by": editor}
        )

        cursor.execute(
            """
            UPDATE tasks
            SET text = ?, updated_at = ?, updated_by = ?, history = ?
            WHERE id = ?
            """,
            (
                new_text,
                edited_at,
                editor,
                json.dumps(entries, ensure_ascii=False),
                task_id,
            ),
        )
        conn.commit()
        return True
