from app.infrastructure.database.models import (
    INSERT_USER,
    GET_USER_BY_ID,
)


class UserRepository:
    def __init__(self, db):
        self.db = db

    async def add_user(self, user_id: int, username: str | None):
        await self.db.conn.execute(
            INSERT_USER,
            (user_id, username),
        )
        await self.db.conn.commit()

    async def get_user(self, user_id: int):
        cursor = await self.db.conn.execute(
            GET_USER_BY_ID,
            (user_id,),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None