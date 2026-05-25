from .commands import commands_router, undefined_router
from .journal_handlers.add_workout import workout_router
from .journal_handlers.journal_operations import journal_router

__all__ = ['routers']

routers = [
    commands_router,
    journal_router,
    workout_router,
    undefined_router
]