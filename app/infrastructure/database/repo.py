import json
import datetime as dt
import logging

from collections import defaultdict
from .database import Database, Transaction
from app.domain.models import Workout, ClimbTrain, GymTrain, Exercise, Route, Row
from app.domain.enums import TrainingCategory, TrainingType
from .sql_models import *

logger = logging.getLogger(__name__)


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

    async def add_journal(
            self, user_id: int,
            comments:str = '',
            period: tuple[dt.date | None, dt.date | None] = (None, None)
            ) -> None:
        await self.db.execute(
            INSERT_JOURNAL,
            (user_id, comments, *period)
            )

    async def get_journal(self, journal_no: int) -> dict | None:
        journal = await self.db.fetchone(
            GET_JOURNAL,
            (journal_no, )
            )

        return dict(journal) if journal else None

    async def get_journals(self, user_id) -> tuple[dict, ...]:
        journals = await self.db.fetchall(
            GET_JOURNALS,
            (user_id, )
        )
        return tuple(dict(j) for j in journals) if journals else tuple()

    async def add_workout(self,
            journal_id: int,
            workout: Workout
    ) -> None:
        async with Transaction(self.db) as db:
            journal = await db.fetchone(
                GET_JOURNAL,
                (journal_id, )
            )
            if journal:
                logger.info(f'dates in journal no.{journal_id}: {journal['period_start'], journal['period_end']}')
                st, en = (dt.date.fromisoformat(journal[t]) or workout.date for t in ['period_start', 'period_end'])
                await db.execute(
                    UPDATE_JOURNAL_PERIOD,
                    (min(st, workout.date), max(en, workout.date), journal_id)
                )
            else:
                return

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

    async def get_workout_by_date(self, date: dt.date) -> Workout | None:
        workout_row = await self.db.fetchone(
            GET_WORKOUT_BY_DATE,
            (date, )
            )
        if not workout_row:
            return
        
        train_rows = await self.db.fetchall(
            GET_TRAINS_BY_WORKOUT,
            (workout_row['workout_id'], )
            )
        train_rows = [dict(row) for row in train_rows]
        train_ids = [x['id'] for x in train_rows]
        if not train_ids:
            return Workout(
                date=dt.date.fromisoformat(workout_row['workout_date']),
                comments=workout_row['comments']
            )

        placeholders = ','.join('?' * len(train_ids))
        rows_rows = await self.db.fetchall(
            GET_ROWS_BY_TRAINS.format(placeholders),
            tuple(train_ids)
            )
        rows_rows = [dict(x) for x in rows_rows]
        row_ids = [x['id'] for x in rows_rows]

        routes_by_row_id = defaultdict(list)
        if row_ids:
            placeholders = ','.join('?' * len(row_ids))
            routes_rows = await self.db.fetchall(
                GET_ROUTES_BY_ROWS.format(placeholders),
                tuple(row_ids)
                )

            for r in routes_rows:
                route = Route(grade=r['grade'], falls=r['falls'], flash=r['flash'])
                routes_by_row_id[r['row_id']].append(route)

        exercises_by_row_id = defaultdict(list)
        if row_ids:
            placeholders = ','.join('?' * len(row_ids))
            exercises_rows = await self.db.fetchall(
                GET_EXERCISES_BY_ROWS.format(placeholders),
                tuple(row_ids)
                )

            for e in exercises_rows:
                exercise = Exercise(name=e['name'], repeats=tuple(json.loads(e['repeats'])))
                exercises_by_row_id[e['row_id']].append(exercise)

        rows_by_train_id = defaultdict(list)
        for row_data in rows_rows:
            row_id = row_data['id']

            content = (
                routes_by_row_id[row_id]
                or exercises_by_row_id[row_id]
                )
            row = Row(
                content=tuple(content),
                comments=row_data['comments']
                )
            rows_by_train_id[row_data['train_id']].append(row)

        trains = []
        for train_data in train_rows:
            train_category = TrainingCategory[train_data['category']]
            train_type = TrainingType[train_data['type']]
            rows = rows_by_train_id[train_data['id']]

            if train_category == TrainingCategory.CLIMBING:
                train = ClimbTrain(
                    type=train_type,
                    rows=rows,
                    comments=train_data['comments']
                    )
            else:
                train = GymTrain(
                    type=train_type,
                    rows=rows,
                    comments=train_data['comments']
                    )

            trains.append(train)

        return Workout(
            date=dt.date.fromisoformat(workout_row['workout_date']),
            content=trains,
            comments=workout_row['comments']
            )
