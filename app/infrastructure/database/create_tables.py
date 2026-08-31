"""
Script to execute before bot polling.
Creates database tables according to the structure described below.

--- DB structure ---
The DB structure mirrors the model hierarchy described in models.py.

Journal -> Workout -> Train -> Row -> Route / Exercise

users(id, tg_id, username, last_journal)
    journals(id, user_id, comments, period_start, period_end)
        workouts(id, journal_id, workout_date, comments)
            trains(id, workout_id, category, type, comments)
                rows(id, train_id, row_order, comments)
                    routes(id, row_id, route_order, grade, falls, flash)
                    exercises(id, row_id, name, repeats)
"""

from .database import Database
from .sql_models import CREATE_INDICIES, SCRIPT_CREATE_TABLES


async def create_tables(db: Database) -> None:
    """Функция запускает SQL-скрипт создания таблиц и включает foreign keys."""

    await db.conn.execute("PRAGMA foreign_keys = ON")
    await db.conn.executescript(SCRIPT_CREATE_TABLES)
    await db.conn.executescript(CREATE_INDICIES)
    await db.conn.commit()
