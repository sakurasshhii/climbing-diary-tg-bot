import aiosqlite
import json
from .database import Database, Transaction
from app.domain.models import Workout, ClimbTrain, GymTrain
from app.domain.enums import TrainingCategory
from .sql_models import (
    INSERT_USER, INSERT_JOURNAL, INSERT_WORKOUT,
    INSERT_TRAIN, INSERT_ROW, INSERT_EXERCISE, INSERT_ROUTE,
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

    async def get_user_by_tg(self, tg_id: int) -> dict | None:
        user = await self.db.fetchone(
            GET_USER_BY_TG_ID,
            (tg_id, )
        )
        return dict(user) if user else None

class JournalRepository:
    '''
    Интерфейс для работы с таблицей Journal и прилежащими
    '''
    def __init__(self, db: Database) -> None:
        self.db = db
    
    async def add_journal(self, user_id: int, comments:str = '') -> None:
        await self.db.execute(
            INSERT_JOURNAL,
            (user_id, comments)
        )

    async def get_journals(self, user_id: int, journal_no: int = False) -> list[dict]:
        journals = await self.db.fetchall(
            GET_JOURNAL,
            (user_id, )
        )
        return [dict(j) for j in journals]
    
    async def add_workout(self,
            journal_id: int,
            workout: Workout
    ) -> None:
        async with Transaction(self.db) as db:
            cursor = await db.execute(
                INSERT_WORKOUT,
                (journal_id, workout.date, workout.comments),
                commit=False
            )
            workout_id = cursor.lastrowid

            for train in workout.content:
                cursor = await db.execute(
                    INSERT_TRAIN,
                    (workout_id, train.training_category.name, train.type.name, train.comments),
                    commit=False
                )

                train_id = cursor.lastrowid

                for i, row in enumerate(train.rows):
                    cursor = await db.execute(
                        INSERT_ROW,
                        (train_id, i, row.comments),
                        commit=False
                    )

                    row_id = cursor.lastrowid

                    if isinstance(train, ClimbTrain):
                        for i_route, route in enumerate(row.content):
                            await db.execute(
                                INSERT_ROUTE,
                                (row_id, i_route, route.grade, route.falls, int(route.flash)),   # type: ignore
                                commit=False
                            )

                    elif isinstance(train, GymTrain):
                        for i_ex, exercise in enumerate(row.content):
                            await db.execute(
                                INSERT_EXERCISE,
                                (row_id, i_ex, exercise.name, json.dumps(exercise.repeats)),   # type: ignore
                                commit=False
                            )