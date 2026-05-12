'''
Код запускается в начале программы для создания таблиц БД.

DB structure:
> users(id, user_id, username)
> journal()
> workout()
> train
> row-set()
> route/exercise()

UI (journal/Workout creation)
1. bttn - where (Journal)
2. bttn - when (date)
3. bttn - kind of training (TrainingType -> Train)
4. input training information (formatted txt where sets separated to new lines)
5. input comment
'''
from .database import Database, Transaction
from .sql_models import CREATE_TABLES


async def create_tables(db: Database) -> None:
    await db.conn.executescript(CREATE_TABLES)
    await db.conn.commit()