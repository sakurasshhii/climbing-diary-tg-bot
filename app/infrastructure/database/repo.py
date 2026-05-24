from __future__ import annotations
import datetime as dt
import json
import logging
from collections import defaultdict

from app.domain.enums import TrainingCategory, TrainingType
from app.domain.models import (
    ClimbTrain,
    Exercise,
    GymTrain,
    Route,
    Row,
    Workout,
)
from .database import Database, Transaction
from .sql_models import *


logger = logging.getLogger(__name__)


class UserRepository:
    """Интерфейс для работы с таблицей users."""

    def __init__(self, db: Database) -> None:
        self.db = db

    async def add_user(self, tg_id: int, username: str | None) -> None:
        """Add user to table users by his telegram id & nickname."""
        await self.db.execute(
            INSERT_USER,
            (tg_id, username),
        )

    async def get_user_by_tg(self, tg_id: int) -> dict | None:
        """Get user from table users by his telegram id."""
        user = await self.db.fetchone(
            GET_USER_BY_TG_ID,
            (tg_id, ),
        )

        return dict(user) if user else None

class JournalRepository:
    """Интерфейс для работы с таблицей journals и связанными."""

    def __init__(self, db: Database) -> None:
        self.db = db

    async def add_journal(
        self, user_id: int,
        comments:str = "",
        period: tuple[dt.date | None, dt.date | None] = (None, None),
    ) -> None:
        """Создает новый пустой journal в таблице journals базы данных."""
        await self.db.execute(
            INSERT_JOURNAL,
            (user_id, comments, *period),
        )

    async def get_journal(self, journal_no: int) -> dict | None:
        """Возвращает информацию о journal пользователя из таблицы journals."""
        journal = await self.db.fetchone(
            GET_JOURNAL,
            (journal_no, ),
        )

        return dict(journal) if journal else None

    async def get_journals(self, user_id: int) -> tuple[dict, ...]:
        """Возвращает все journals пользователя по его id."""
        journals = await self.db.fetchall(
            GET_JOURNALS,
            (user_id, ),
        )

        return tuple(dict(j) for j in journals) if journals else tuple()

    async def add_workout(
            self,
            journal_id: int,
            workout: Workout,
    ) -> None:
        """Добавляет данные о Workout в БД."""
        async with Transaction(self.db) as db:
            journal = await db.fetchone(
                GET_JOURNAL,
                (journal_id, ),
            )

            if not journal:
                return

            st, en = (
                (
                    dt.date.fromisoformat(journal[date])
                    if journal[date]
                    else workout.date
                ) for date in ("period_start", "period_end")
            )

            await db.execute(
                UPDATE_JOURNAL_PERIOD,
                (min(st, workout.date), max(en, workout.date), journal_id),
            )

            cursor = await db.execute(
                INSERT_WORKOUT,
                (journal_id, workout.date, workout.comments),
                commit=False,
            )

            workout_id = cursor.lastrowid

            for train in workout.content:
                cursor = await db.execute(
                    INSERT_TRAIN,
                    (workout_id, train.training_category.name, train.type.name, train.comments),
                    commit=False,
                )

                train_id = cursor.lastrowid

                for row_index, row in enumerate(train.rows):
                    cursor = await db.execute(
                        INSERT_ROW,
                        (train_id, row_index, row.comments),
                        commit=False,
                    )

                    row_id = cursor.lastrowid

                    if isinstance(train, ClimbTrain):
                        for route_index, route in enumerate(row.content):
                            if not isinstance(route, Route):
                                logger.warning(
                                    "Данные из БД не соответствуют ожидаемому типу данных " \
                                    "Route: {}".format(type(route))
                                )
                                raise TypeError
                            await db.execute(
                                INSERT_ROUTE,
                                (row_id, route_index, route.grade, route.falls, int(route.flash)),
                                commit=False,
                            )

                    elif isinstance(train, GymTrain):
                        for i_ex, exercise in enumerate(row.content):
                            if not isinstance(exercise, Exercise):
                                logger.warning("Данные из БД не соответствуют ожидаемому типу данных " \
                                    "Exercise: {}".format(type(exercise))
                                )
                                raise TypeError
                            await db.execute(
                                INSERT_EXERCISE,
                                (row_id, i_ex, exercise.name, json.dumps(exercise.repeats)),
                                commit=False,
                            )

    async def get_workout_by_date(self, date: dt.date) -> Workout | None:
        """Создает запрос к БД и возвращает Workout по дате."""
        workout_row = await self.db.fetchone(
            GET_WORKOUT_BY_DATE,
            (date, ),
        )

        if not workout_row:
            return None

        train_rows = await self.db.fetchall(
            GET_TRAINS_BY_WORKOUT,
            (workout_row["workout_id"], ),
        )

        train_rows = [dict(row) for row in train_rows]
        train_ids = [row["id"] for row in train_rows]

        if not train_ids:
            return Workout(
                date=dt.date.fromisoformat(workout_row["workout_date"]),
                comments=workout_row["comments"],
            )

        placeholders = ",".join("?" * len(train_ids))

        rows_rows = await self.db.fetchall(
            GET_ROWS_BY_TRAINS.format(placeholders),
            tuple(train_ids),
        )
        rows_rows = [dict(row) for row in rows_rows]
        row_ids = [row["id"] for row in rows_rows]

        routes_by_row_id = defaultdict(list)
        if row_ids:
            placeholders = ",".join("?" * len(row_ids))
            routes_rows = await self.db.fetchall(
                GET_ROUTES_BY_ROWS.format(placeholders),
                tuple(row_ids),
            )

            for r in routes_rows:
                route = Route(grade=r["grade"], falls=r["falls"], flash=r["flash"])
                routes_by_row_id[r["row_id"]].append(route)

        exercises_by_row_id = defaultdict(list)
        if row_ids:
            placeholders = ",".join("?" * len(row_ids))
            exercises_rows = await self.db.fetchall(
                GET_EXERCISES_BY_ROWS.format(placeholders),
                tuple(row_ids),
                )

            for e in exercises_rows:
                exercise = Exercise(
                    name=e["name"],
                    repeats=tuple(json.loads(e["repeats"]))
                )
                exercises_by_row_id[e["row_id"]].append(exercise)

        rows_by_train_id = defaultdict(list)
        for row_data in rows_rows:
            row_id = row_data["id"]

            content = (
                routes_by_row_id[row_id]
                or exercises_by_row_id[row_id]
            )
            row = Row(
                content=tuple(content),
                comments=row_data["comments"],
            )
            rows_by_train_id[row_data["train_id"]].append(row)

        trains = []
        for train_data in train_rows:
            train_category = TrainingCategory[train_data["category"]]
            train_type = TrainingType[train_data["type"]]
            rows = rows_by_train_id[train_data["id"]]

            if train_category == TrainingCategory.CLIMBING:
                train = ClimbTrain(
                    type=train_type,
                    rows=rows,
                    comments=train_data["comments"],
                )
            else:
                train = GymTrain(
                    type=train_type,
                    rows=rows,
                    comments=train_data["comments"],
                )

            trains.append(train)

        return Workout(
            date=dt.date.fromisoformat(workout_row["workout_date"]),
            content=trains,
            comments=workout_row["comments"],
        )
