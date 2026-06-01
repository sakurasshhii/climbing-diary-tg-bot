from __future__ import annotations

import datetime as dt
import json
import logging
from collections import defaultdict
from collections.abc import Iterable, Mapping

from app.domain.models import (ClimbTrain, DBJournal, DBRow, DBTrain,
                               DBWorkout, Exercise, GymTrain, Route, Row,
                               Workout, Train, Journal)
from app.domain.enums import TrainingCategory, TrainingType

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

    async def get_journal(self, journal_no: int) -> DBJournal | None:
        """Возвращает информацию о journal пользователя из таблицы journals."""
        journal = await self.db.fetchone(
            GET_JOURNAL,
            (journal_no, ),
        )
        if journal is None:
            return None

        return DBJournal(**dict(journal))
    
    async def get_journal_full(self, journal_id: int) -> Journal | None:
        GET_J_FROM_JOURNALS = """
            SELECT * FROM journals
            WHERE id=?;"""
        GET_J_WORKOUTS = """
            SELECT *
            FROM workouts
            WHERE journal_id=?
            ORDER BY workout_date;"""
        GET_J_TRAINS = """
            SELECT t.*
            FROM trains t
            JOIN workouts w
                ON w.id=t.workout_id
            WHERE w.journal_id=?
            ORDER BY t.id;"""
        GET_J_ROWS = """
            SELECT r.*
            FROM rows r
            JOIN trains t
                ON t.id = r.train_id
            JOIN workouts w
                ON w.id = t.workout_id
            WHERE w.journal_id = ?
            ORDER BY
                r.train_id,
                r.row_order;
            """
        GET_J_ROUTES = """
            SELECT
                rt.*
            FROM routes rt
            JOIN rows r
                ON r.id = rt.row_id
            JOIN trains t
                ON t.id = r.train_id
            JOIN workouts w
                ON w.id = t.workout_id
            WHERE w.journal_id = ?
            ORDER BY
                rt.row_id,
                rt.route_order;
            """
        GET_J_EXERCISES = """
            SELECT
                ex.*
            FROM exercises ex
            JOIN rows r
                ON r.id = ex.row_id
            JOIN trains t
                ON t.id = r.train_id
            JOIN workouts w
                ON w.id = t.workout_id
            WHERE w.journal_id = ?
            ORDER BY
                ex.row_id,
                ex.exercise_order;
            """
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
        
        routes_by_row = defaultdict(list)
        for r in routes:
            route = Route(
                grade=r["grade"],
                falls=r["falls"],
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
                        type=tr.type,
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
            content=workouts,
            comments=db_journal.comments or ""
        )

    async def get_journals(self, user_id: int) -> Iterable[DBJournal]:
        """Возвращает все journals пользователя по его id."""
        journals = await self.db.fetchall(
            GET_JOURNALS,
            (user_id, ),
        )
        return tuple(DBJournal(**j) for j in journals)

    async def get_workouts(self, journal_id: int) -> Iterable[DBWorkout]:
        """Возвращает все workouts из journal."""
        raw_workouts = await self.db.fetchall(
            GET_WORKOUTS,
            (journal_id,),
        )
        return tuple(DBWorkout(**w) for w in raw_workouts if w)

    # async def get_trains(self, workout_ids: Iterable[int]) -> Mapping[int, list[DBTrain]]:
    #     """Возвращает все trains из workouts в виде словаря, где ключами являются workout.id."""
    #     ids = tuple(workout_ids)
    #     placeholders = self._get_placeholders(len(ids))
    #     rows = await self.db.fetchall(
    #         GET_TRAINS_BY_WORKOUTS.format(placeholders),
    #         ids,
    #     )

    #     grouped = defaultdict(list)
    #     for tr in rows:
    #         train = DBTrain(**dict(tr))
    #         grouped[train.workout_id].append(tr)

    #     return grouped

    async def get_trains(self, workout_id: int) -> Iterable[DBTrain]:
        """Возвращает все trains из workout."""
        raw_train = await self.db.fetchall(
            GET_TRAINS_BY_WORKOUT,
            (workout_id,),
        )
        return tuple(DBTrain(**t)for t in raw_train if t)

    async def get_rows(self, train: DBTrain) -> tuple[DBRow, ...]:
        """Возвращает список с подходами для trains."""
        raw_rows = await self.db.fetchall(
            GET_ROWS_BY_TRAINS.format("?"),
            (train.workout_id,),
        )
        raw_rows = [DBRow(**dict(r)) for r in raw_rows]
        return tuple(raw_rows)

    async def get_routes(self, rows: Iterable[DBRow]) -> Mapping[int, Iterable[Route]]:
        """Возвращает список трасс по индексам подходов."""
        row_ids = [row.id for row in rows]
        routes_by_row_id: dict[int, list[Route]] = defaultdict(list)
        placeholders = self._get_placeholders(len(row_ids))

        raw_routes = await self.db.fetchall(
            GET_ROUTES_BY_ROWS.format(placeholders),
            tuple(row_ids),
        )
        for route in raw_routes:
            routes_by_row_id[route["row_id"]].append(
                Route(grade=route["grade"], falls=route["falls"], flash=bool(route["flash"]))
            )

        return routes_by_row_id

    async def get_exercises(self, rows: Iterable[DBRow]) -> Mapping[int, Iterable[Exercise]]:
        """Возвращает список упражнений по индексам подходов."""
        row_ids = [row.id for row in rows]
        exercises_by_row_id = defaultdict(list)
        placeholders = ",".join("?" * len(row_ids))

        raw_exercises = await self.db.fetchall(
            GET_EXERCISES_BY_ROWS.format(placeholders),
            tuple(row_ids),
        )
        for ex in raw_exercises:
            exercises_by_row_id[ex["row_id"]].append(
                Exercise(
                    name=ex["name"],
                    repeats=tuple(json.loads(ex["repeats"]))
                )
            )

        return exercises_by_row_id

    def _get_placeholders(self, n: int) -> str:
        return ",".join("?" * n)