"""Пакет для работы с базой данных."""

from .database import add_task, get_all_tasks, init_db

__all__ = ["init_db", "add_task", "get_all_tasks"]
