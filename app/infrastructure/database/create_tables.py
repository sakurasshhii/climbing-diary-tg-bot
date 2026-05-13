'''
Script to execute before bot polling.
Creates database tables according to the structure described below.

--- DB structure ---
The DB structure mirrors the model hierarchy described in models.py.

Journal -> Workout -> Train -> Row -> Route / Exercise

> users(id, user_id, username)
    > journals(id, user_id, comments)
        > workouts(id, journal_id, workout_date, comments)
            > trains(id, workout_id, category, type, comments)
                > rows(id, train_id, row_order, comments)
                    > routes(id, row_id, route_order, grade, falls, flash)
                    > exercises(id, row_id, name, repeats)
'''
from .database import Database, Transaction
from .sql_models import SCRIPT_CREATE_TABLES


async def create_tables(db: Database) -> None:
    await db.conn.execute('PRAGMA foreign_keys = ON')
    await db.conn.executescript(SCRIPT_CREATE_TABLES)
    await db.conn.commit()