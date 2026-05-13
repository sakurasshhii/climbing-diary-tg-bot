import aiosqlite
from .database import Database, Transaction
from .sql_models import (
    INSERT_USER, INSERT_JOURNAL,
    GET_USER_BY_TG_ID, GET_JOURNAL, GET_USER_ID,
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
    def __init__(self, db: Database) -> None:
        self.db = db

    async def add_user(self, tg_id: int, username: str | None) -> None:
        await self.db.execute(
            INSERT_USER,
            (tg_id, username)
        )

    async def get_user(self, tg_id: int) -> aiosqlite.Row | None:
        user = await self.db.fetchone(
            GET_USER_BY_TG_ID,
            (tg_id, )
        )
        return user

    async def get_user_assured(self, tg_id: int, username='') -> aiosqlite.Row:
        user = await self.get_user(tg_id)
        if user:
            return user
        
        await self.add_user(
            tg_id=tg_id,
            username=username
        )
        return await self.get_user(tg_id) # type: ignore
    
    async def add_journal(self, tg_id: int, comments:str = '') -> None:
        user_id = await self._get_user_id(tg_id)
        await self.db.execute(
            INSERT_JOURNAL,
            (user_id, comments)
        )

    async def get_journals(self, tg_id: int, journal_no: int = False):
        user_id = await self._get_user_id(tg_id)
        journal = await self.db.fetchall(
            GET_JOURNAL,
            (user_id, )
        )
        return journal
    
    async def _get_user_id(self, tg_id: int) -> int | None:
        user_id = await self.db.fetchone(
            GET_USER_ID,
            (tg_id, )
        )
        return user_id[0] if user_id else None
