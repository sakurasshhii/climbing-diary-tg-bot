import aiosqlite
import logging

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, connection: aiosqlite.Connection) -> None:
        self.conn = connection
    
    async def execute(self, query, params=None, commit=True):
        'Для запросов: INSERT, UPDATE, DELETE, CREATE TABLE'
        await self.conn.execute(query, params or [])
        if commit:
            await self.conn.commit()

    async def fetchone(self, query, params=None):
        'Возвращает одну строку из результата запроса'
        cursor = await self.conn.execute(query, params or [])
        return await cursor.fetchone()

    async def fetchall(self, query, params=None):
        'Возвращает все строки результата запроса'
        cursor = await self.conn.execute(query, params or [])
        return await cursor.fetchall()
