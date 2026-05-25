import asyncio
import datetime as dt
from collections.abc import Iterable

from app.infrastructure.database.repo import UserRepository, JournalRepository
from app.domain.models import (
    Journal, Workout, User, ClimbTrain, GymTrain, Row,
    DBJournal, DBWorkout, DBTrain,
)
from app.domain.exceptions import UserNotFoundError
from app.domain.enums import TrainingType, TrainingCategory
from app.bot.states.add_workout import FSMWorkoutDataComplete
from .parser import JournalParser


class UserService:
    def __init__(self, user_repo: UserRepository) -> None:
        self.user_repo = user_repo
    
    async def add_user(self, tg_id: int, username: str | None) -> None:
        await self.user_repo.add_user(tg_id=tg_id, username=username)

    async def get_user(self, tg_id: int) -> User | None:
        req = await self.user_repo.get_user_by_tg(tg_id=tg_id)
        if not req:
            return

        user = User(
            id = req['id'],
            tg_id = req['tg_id'],
            username = req['username'],
            last_journal = req['last_journal']
        )
        return user

    async def get_user_assured(self, tg_id: int, username='') -> User:
        user = await self.get_user(tg_id)
        if user:
            return user

        await self.add_user(
            tg_id=tg_id,
            username=username
        )
        return await self.get_user(tg_id) # type: ignore

class JournalService:
    def __init__(
        self, user_repo: UserRepository,
        journal_repo: JournalRepository
    ) -> None:
        self.user_repo = user_repo
        self.journal_repo = journal_repo

    async def add_journal(self, tg_id: int, comments:str = '') -> None:
        user = await self.user_repo.get_user_by_tg(tg_id)
        if not user:
            raise UserNotFoundError(tg_id)
        await self.journal_repo.add_journal(user_id=user['id'], comments=comments)

    async def add_workout(
        self,
        tg_id: int,
        data: FSMWorkoutDataComplete
    ) -> None:
        user = await self.user_repo.get_user_by_tg(tg_id)
        if not user:
            raise UserNotFoundError(tg_id)

        workout = JournalParser.parse_workout(
            workout_date=data['workout_date'],
            training_category=data['training_category'],
            training_type=data['training_type'],
            content=data['content'],
            comments=data['comments']
        )
        await self.journal_repo.add_workout(
            journal_id=data['journal_no'],
            workout=workout
        )

    async def get_journals(self, tg_id: int) -> Iterable[DBJournal]:
        """Возвращает все journals пользователя по его id."""
        user = await self.user_repo.get_user_by_tg(tg_id)
        if not user:
            raise UserNotFoundError(tg_id)
        return await self.journal_repo.get_journals(user['id'])

    async def get_journal(self, journal_id: int) -> Journal:
        """Возвращает Journal пользователя."""
        journal_raw = await self.journal_repo.get_journal(journal_id)
        if journal_raw is None:
            raise ValueError("Journal not found.")

        raw_workouts = await self.journal_repo.get_workouts(journal_raw.id)
        workouts = await asyncio.gather(*[self.get_workout(w) for w in raw_workouts])

        return Journal(content=workouts, comments=journal_raw.comments)

    async def get_workout(self, work_raw: DBWorkout) -> Workout:
        """Возвращает Workout пользователя по id."""
        raw_trains: Iterable[DBTrain] = await self.journal_repo.get_trains(work_raw.id)

        workout = Workout(
            date=work_raw.workout_date,
            comments=work_raw.comments
        )

        for tr_raw in raw_trains:
            rows_raw = await self.journal_repo.get_rows(tr_raw)
            match tr_raw.category:
                case TrainingCategory.CLIMBING:
                    content_all = await self.journal_repo.get_routes(rows_raw)
                    rows = [
                        Row(
                            content=tuple(content_all[j]),
                            comments=rows_raw[i].comments
                        )
                        for i, j in enumerate(content_all)
                    ]
                    train = ClimbTrain(
                        type=tr_raw.type,
                        rows=rows,
                        comments=tr_raw.comments
                    )
                case TrainingCategory.GYM:
                    content_all = await self.journal_repo.get_exercises(rows_raw)
                    rows = [
                        Row(
                            content=tuple(content_all[j]),
                            comments=rows_raw[i].comments
                        )
                        for i, j in enumerate(content_all)
                    ]
                    train = GymTrain(
                        type=tr_raw.type,
                        rows=rows,
                        comments=tr_raw.comments
                    )
                case _:
                    raise ValueError(f"Undefined TrainingCategory: {tr_raw.category}")

            workout.add_train(
                train
            )

        return workout

    @staticmethod
    def training_sets_validation(text: str, training_cat: TrainingCategory) -> bool:
        return bool(JournalParser.is_valid_rows(text, training_category=training_cat))
