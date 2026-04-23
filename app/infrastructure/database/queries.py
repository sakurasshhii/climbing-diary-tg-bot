from app.infrastructure.database.database import Database, Transaction
from app.infrastructure.database.models import (
    INSERT_USER,
    GET_USER_BY_ID,
)


class UserRepository:
    def __init__(self, db: Database):
        self.db = db

    async def add_user(self, user_id: int, username: str | None):
        await self.db.execute(
            INSERT_USER,
            (user_id, username),
        )

    async def get_user(self, user_id: int):
        row = await self.db.fetchone(
            GET_USER_BY_ID,
            (user_id,),
        )
        return dict(row) if row else None
    
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