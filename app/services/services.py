import logging
from collections.abc import Iterable, Sequence

from app.domain.enums import TrainingCategory, TrainingType
from app.domain.exceptions import UserNotFoundError
from app.domain.models import (ClimbTrain, DBJournal, DBTrain, DBWorkout,
                               GymTrain, Journal, Row, User, Workout)
from app.infrastructure.database.repo import JournalRepository, UserRepository

from .parser import JournalParser

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self, user_repo: UserRepository) -> None:
        self.user_repo = user_repo
    
    async def add_user(self, tg_id: int, username: str | None) -> None:
        await self.user_repo.add_user(tg_id=tg_id, username=username)
        # logger.info(
        #     "AFTER INSERT USER: %s",
        #     await self.user_repo.get_all_users()
        # )

    async def get_all_users(self) -> Iterable[User]:
        users = await self.user_repo.get_all_users()
        return users

    async def get_user(self, tg_id: int) -> User | None:
        return await self.user_repo.get_user_by_tg(tg_id=tg_id)

    async def get_user_assured(self, tg_id: int, username="") -> User:
        user = await self.get_user(tg_id)
        if user:
            return user

        n = 0
        while user is None:
            n += 1
            if n == 5:
                logger.warning("DATABASE PROBLEM: can't add user to db :(")
                raise RuntimeError
            await self.add_user(
                tg_id=tg_id,
                username=username
            )
            user = await self.get_user(tg_id)

        return user

class JournalService:
    def __init__(
        self, user_repo: UserRepository,
        journal_repo: JournalRepository
    ) -> None:
        self.user_repo = user_repo
        self.journal_repo = journal_repo

    async def add_journal(
            self,
            tg_id: int,
            name: str = "",
            comments: str = "",
        ) -> None:
        user = await self.user_repo.get_user_by_tg(tg_id, raise_err=True)

        if comments in ("-", "—"):
            comments = ""

        await self.journal_repo.add_journal(
            user_id=user.id, # type: ignore
            name=name,
            comments=comments,
        )

    async def add_workout(self, data: FSMWorkoutDataComplete ) -> None: # type: ignore
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

    async def get_journals(self, tg_id: int) -> Sequence[DBJournal]:
        """Возвращает все journals пользователя по его id."""
        user = await self.user_repo.get_user_by_tg(tg_id, raise_err=True)

        journals = await self.journal_repo.get_journals(user.id) # type: ignore
        logger.info("JOURNALS: %s", tuple(journals))
        return journals

    async def get_journals_by_ids(self, ids: Sequence[int]) -> Sequence[DBJournal]:
        """Возвращвет список указанных journals."""
        journals = await self.journal_repo.get_journals_by_ids(ids)

        return journals

    async def get_journal(self, journal_id: int) -> DBJournal:
        journal = await self.journal_repo.get_journal(journal_id)
        if journal is None:
            logger.exception("Journal not found: %s", journal_id)
            raise ValueError("Journal not found")
        return journal

    async def get_complete_journal(self, journal_id: int) -> Journal | None:
        """Возвращает Journal пользователя."""
        journal = await self.journal_repo.get_complete_journal(journal_id)
        if journal is None:
            raise ValueError("Journal not found")

        return journal

    async def delete_journals(self, tg_id: int, del_list: Sequence[int]) -> None:
        if not del_list:
            return

        user = await self.user_repo.get_user_by_tg(tg_id, raise_err=True)
        await self.journal_repo.delete_journals(user.id, del_list) # type: ignore

    @staticmethod
    def training_sets_validation(text: str, training_cat: TrainingCategory) -> bool:
        return bool(JournalParser.parse_rows(text, training_category=training_cat))
