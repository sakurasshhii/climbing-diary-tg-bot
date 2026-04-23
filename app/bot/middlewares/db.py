from aiogram import BaseMiddleware
from typing import Callable, Dict, Any, Awaitable

from app.infrastructure.database.queries import UserRepository


class DbMiddleware(BaseMiddleware):
    def __init__(self, db):
        self.users_repo = UserRepository(db)

    async def __call__(
        self,
        handler: Callable,
        event,
        data: Dict[str, Any]
    ) -> Awaitable[Any]:
        data["users"] = self.users_repo
        return await handler(event, data)