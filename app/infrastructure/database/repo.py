from __future__ import annotations

import datetime as dt
import json
import logging
from collections import defaultdict
from collections.abc import Iterable, Sequence

from app.domain.models import (ClimbTrain, DBJournal, DBRow, DBTrain,
                               DBWorkout, Exercise, GymTrain, Journal, Route,
                               Row, Train, User, Workout)

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

    async def get_all_users(self) -> Iterable[User]:
        users = await self.db.fetchall(
            """SELECT *
            FROM users
            """
        )

        return tuple(User(**u) for u in users)

    async def get_user_by_tg(self, tg_id: int) -> User | None:
        """Get user from table users by his telegram id."""
        user = await self.db.fetchone(
            GET_USER_BY_TG_ID,
            (tg_id, ),
        )

        return User(**user) if user else None

class JournalRepository:
    """Интерфейс для работы с таблицей journals и связанными."""

    def __init__(self, db: Database) -> None:
        self.db = db

    async def add_journal(
        self,
        user_id: int,
        name: str = "",
        comments: str = "",
        period: tuple[dt.date | None, dt.date | None] = (None, None),
    ) -> None:
        """Создает новый пустой journal в таблице journals базы данных."""
        logger.info("CREATE JOURNAL, args: %s", (user_id, name, comments, *period))
        await self.db.execute(
            INSERT_JOURNAL,
            (user_id, name, comments, *period),
        )

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
                                (row_id, route_index, route.grade, route.falls_no, int(route.flash)),
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

    async def get_journal(self, journal_no: int) -> DBJournal | None:
        """Возвращает информацию о journal пользователя из таблицы journals."""
        journal = await self.db.fetchone(
            GET_JOURNAL,
            (journal_no, ),
        )
        if journal is None:
            return None

        return DBJournal(**dict(journal))

    async def get_journals(self, user_id: int) -> Sequence[DBJournal]:
        """Возвращает все journals пользователя по его id."""
        journals = await self.db.fetchall(
            GET_JOURNALS,
            (user_id, ),
        )
        return tuple(DBJournal(**j) for j in journals)

    async def get_complete_journal(self, journal_id: int) -> Journal | None:
        """Собирает и возвращает Journal с полной информацией о тренировках."""
        async with Transaction(self.db) as db:
            db_journal = await db.fetchone(GET_J_FROM_JOURNALS, (journal_id,))
            if not db_journal:
                return None

            db_journal = DBJournal(**db_journal)
            db_workouts = await db.fetchall(GET_J_WORKOUTS, (journal_id,))
            trains = await db.fetchall(GET_J_TRAINS, (journal_id,))
            rows = await db.fetchall(GET_J_ROWS, (journal_id,))
            routes = await db.fetchall(GET_J_ROUTES, (journal_id,))
            exercises = await db.fetchall(GET_J_EXERCISES, (journal_id,))

            logger.info("%s: SQL query count: 5", __name__)

        routes_by_row = defaultdict(list)
        for r in routes:
            route = Route(
                grade=r["grade"],
                falls_no=r["falls"],
                flash=bool(r["flash"]),
            )
            routes_by_row[r["row_id"]].append(route)

        exercises_by_row = defaultdict(list)
        for e in exercises:
            ex = Exercise(
                name=e["name"],
                repeats=tuple(json.loads(e["repeats"]))
            )
            exercises_by_row[e["row_id"]].append(ex)

        rows_by_train = defaultdict(list)
        for r in rows:
            r = DBRow(**r)
            content = tuple(routes_by_row[r.id]) if routes_by_row[r.id] \
                else tuple(exercises_by_row[r.id])
            rows_by_train[r.train_id].append(Row(content=content, comments=r.comments))

        trains_by_workout = defaultdict(list)
        for tr in trains:
            tr = DBTrain(**tr)
            try:
                trains_by_workout[tr.id].append(
                    Train.from_training_category(
                        training_category=tr.category,
                        tr_type=tr.type,
                        rows=rows_by_train[tr.id],
                        comments=tr.comments or "",
                    )
                )
            except TypeError as e:
                logger.error("WRONG DATABASE TYPE. ENUM NEEDED: %s %s", tr.category, tr.type)

        workouts = []
        for w in db_workouts:
            w = DBWorkout(**w)
            workouts.append(Workout(
                date=w.workout_date,
                content=trains_by_workout[w.id],
                comments=w.comments or "",
            ))

        return Journal(
            name = db_journal.name,
            content=workouts,
            comments=db_journal.comments or ""
        )
