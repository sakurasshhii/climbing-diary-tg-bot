import aiosqlite
import logging

logger = logging.getLogger(__name__)


class Database:
    '''
    Класс для выполнения SQL-запросов.
    '''
    def __init__(self, connection: aiosqlite.Connection) -> None:
        self.conn = connection
    
    async def execute(self, query: str, params: tuple | None = None,
                      commit=True) -> aiosqlite.Cursor:
        'Для запросов: INSERT, UPDATE, DELETE, CREATE TABLE'
        result = await self.conn.execute(query, params or [])
        if commit:
            await self.conn.commit()
        return result

    async def fetchone(self, query: str, params: tuple | None = None):
        'Возвращает одну строку из результата запроса'
        cursor = await self.conn.execute(query, params or [])
        return await cursor.fetchone()

    async def fetchall(self, query: str, params: tuple | None = None):
        'Возвращает все строки результата запроса'
        cursor = await self.conn.execute(query, params or [])
        return await cursor.fetchall()

class Transaction:
    '''
    Класс для работы с транзакциями.
    '''
    def __init__(self, db: Database) -> None:
        self.db = db
    
    async def __aenter__(self) -> Database:
        await self.db.conn.execute('BEGIN')
        return self.db

    async def __aexit__(self, exc_type, exc, tb):
        if exc:
            await self.db.conn.rollback()
        else:
            await self.db.conn.commit()