import aiosqlite
import logging

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, path: str) -> None:
        self.path = path
        self._conn: aiosqlite.Connection | None = None
    
    @property
    def conn(self) -> aiosqlite.Connection:
        if self._conn is None:
            logger.error('Database not connected')
            raise RuntimeError
        else:
            return self._conn
    
    @conn.setter
    def conn(self, connection) -> None:
        if isinstance(connection, aiosqlite.Connection):
            self._conn = connection
    
    async def connect(self):
        self.conn = await aiosqlite.connect(self.path)
        await self.conn.execute('PRAGMA journal_mode=WAL;')
        # self.conn.row_factory = aiosqlite.Row
        
    async def close(self):
        if self.conn:
            await self.conn.close()
