from .commands import commands_router, undefined_router
from .journal_handlers.add_journal import journal_add_router
from .journal_handlers.add_workout import workout_router
from .journal_handlers.get_journal import journal_get_router
from .journal_handlers.edit_journals import journal_edit_router

__all__ = ['routers']

routers = [
    commands_router,
    journal_get_router,
    journal_add_router,
    journal_edit_router,
    workout_router,
    undefined_router,
]