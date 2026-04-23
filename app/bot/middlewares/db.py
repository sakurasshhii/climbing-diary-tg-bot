from aiogram import BaseMiddleware
from typing import Callable, Dict, Any, Awaitable

from app.infrastructure.database.repo import UserRepository
from app.infrastructure.database import Database


class DBUserMiddleware(BaseMiddleware):
    '''
    Проброс работы с user_repo в хэндлер.
    '''
    def __init__(self, db: Database):
        self.db = db

    async def __call__(
        self,
        handler: Callable,
        event,
        data: Dict[str, Any]
    ) -> Awaitable[Any]:
        user_repo: UserRepository = UserRepository(self.db)
        data["user_repo"] = user_repo
        return await handler(event, data)