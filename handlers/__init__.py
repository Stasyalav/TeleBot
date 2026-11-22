"""Пакет с обработчиками команд (роутерами)."""

from .start import router as start_router
from .tasks import router as tasks_router

__all__ = ["start_router", "tasks_router"]
