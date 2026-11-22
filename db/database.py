"""Функции для работы с SQLite3.

Здесь создаётся таблица tasks и выполняются основные операции:
- добавить задачу;
- получить список всех задач.
"""

import sqlite3
from datetime import datetime

from config import DB_PATH


def get_connection() -> sqlite3.Connection:
    """Создаёт подключение к базе данных SQLite."""
    # check_same_thread=False позволяет использовать соединение в разных местах,
    # но для простоты в этом примере мы открываем соединение на каждую операцию.
    return sqlite3.connect(DB_PATH)


def init_db() -> None:
    """Создаёт таблицу tasks, если её ещё нет."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                user TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


def add_task(text: str, user: str) -> int:
    """Сохраняет новую задачу в базу и возвращает её ID."""
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO tasks (text, user, created_at) VALUES (?, ?, ?)",
            (text, user, created_at),
        )
        conn.commit()
        # lastrowid содержит ID добавленной строки.
        return int(cursor.lastrowid)


def get_all_tasks() -> list[tuple[int, str, str, str]]:
    """Возвращает все задачи из базы.

    Каждая задача — это кортеж: (id, text, user, created_at).
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, text, user, created_at FROM tasks ORDER BY id ASC"
        )
        return cursor.fetchall()
