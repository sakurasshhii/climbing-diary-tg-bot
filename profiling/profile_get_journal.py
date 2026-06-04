import asyncio

import aiosqlite

from app.infrastructure.database.create_tables import create_tables
from app.infrastructure.database.database import Database
from app.infrastructure.database.repo import JournalRepository, UserRepository
from app.services.services import JournalService


async def scenario():
    # ———————————————————————— init db ——————————————————————
    db = await aiosqlite.connect(r'app\infrastructure\database\db_data\climbing.db')
    db.row_factory = aiosqlite.Row
    my_db = Database(db)
    await create_tables(db=my_db)

    # ————————————————————————— init service ——————————————————————————
    user_repo: UserRepository = UserRepository(my_db)
    journal_repo: JournalRepository = JournalRepository(my_db)

    service: JournalService = JournalService(user_repo=user_repo, journal_repo=journal_repo)

    # ————————————————————————— profile ——————————————————————————
    for _ in range(100):
        await service.get_complete_journal(1)


if __name__ == "__main__":
    asyncio.run(scenario())
