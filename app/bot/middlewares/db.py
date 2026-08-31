from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware

from app.infrastructure.database import Database
from app.infrastructure.database.repo import JournalRepository, UserRepository
from app.services.services import JournalService, UserService


class ServicesMiddleware(BaseMiddleware):
    '''
    Проброс работы с сервисов в хэндлер.
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
        journal_repo: JournalRepository = JournalRepository(self.db)
        
        user_service: UserService = UserService(user_repo=user_repo)
        journal_service: JournalService = JournalService(user_repo=user_repo, journal_repo=journal_repo)

        data['user_service'] = user_service
        data['journal_service'] = journal_service

        return await handler(event, data)