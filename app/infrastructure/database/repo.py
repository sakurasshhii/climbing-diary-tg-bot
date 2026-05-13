from .database import Database, Transaction
from .sql_models import (
    INSERT_USER,
    GET_USER_BY_ID,
)

'''
Пример использования Transaction
async def add_get_user(self, user_id: int, username: str | None):
    async with Transaction(self.db) as db:
        await db.execute(
            INSERT_USER,
            (user_id, username),
            commit=False
        )
        row = await self.db.fetchone(
            GET_USER_BY_ID,
            (user_id,),
        )
    return dict(row) if row else None'''


class UserRepository:
    '''
    Интерфейс для работы с таблицей users
    '''
    def __init__(self, db: Database):
        self.db = db

    async def add_user(self, user_id: int, username: str | None):
        await self.db.execute(
            INSERT_USER,
            (user_id, username)
        )

    async def get_user(self, user_id: int):
        user = await self.db.fetchone(
            GET_USER_BY_ID,
            (user_id,)
        )
        return dict(user) if user else None
