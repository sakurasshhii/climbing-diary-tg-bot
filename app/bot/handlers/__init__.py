from .commands import commands_router
from .journal_handlers import journal_router

__all__ = ['routers']

routers = [
    commands_router,
    journal_router
]