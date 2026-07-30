import logging
from collections.abc import Iterable, Sequence

from app.domain.models import (DBJournal, Journal, User)
from app.infrastructure.database.repo import JournalRepository, UserRepository
from app.infrastructure.database.exceptions import UserNotFoundError, JournalNotFoundError, WorkoutError

from .parser import JournalParser

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self, user_repo: UserRepository) -> None:
        self.user_repo = user_repo
    
    async def add_user(self, tg_id: int, username: str | None) -> None:
        await self.user_repo.add_user(tg_id=tg_id, username=username)

    async def get_all_users(self) -> Iterable[User]:
        users = await self.user_repo.get_all_users()
        return users

    async def get_user(self, tg_id: int) -> User | None:
        return await self.user_repo.get_user_by_tg(tg_id=tg_id)

    async def get_user_assured(self, tg_id: int, username="") -> User:
        user = await self.get_user(tg_id)
        if user:
            return user

        await self.add_user(
                tg_id=tg_id,
                username=username
            )

        user = await self.get_user(tg_id)

        if user is None:
            logger.warning("DATABASE PROBLEM: can't add user to db :(")
            raise RuntimeError

        return user

class JournalService:
    def __init__(
        self, user_repo: UserRepository,
        journal_repo: JournalRepository
    ) -> None:
        self.user_repo = user_repo
        self.journal_repo = journal_repo
        self.parser = JournalParser()

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

    async def check_workout_in_journal(self, workout_date, journal_id) -> bool:
        """Check if workout with the same date already exists in chosen journal."""
        return await self.journal_repo.check_workout_in_journal(
                workout_date,
                journal_id
            )

    async def add_workout(self, data: FSMWorkoutDataComplete, allow_duplicate=True) -> None: # type: ignore
        """Добавляет данные о тренировке в указанный журнал."""
        if allow_duplicate is False:
            if await self.check_workout_in_journal(
                data["workout_date"],
                data["journal_no"],
            ):
                raise WorkoutError(f"Workout with that date already exists: {data['workout_date']}")

        content = self.parser.loads_sets(data['content'], data['training_category'])
        workout = JournalParser.parse_workout(
            workout_date=data['workout_date'],
            training_category=data['training_category'],
            training_type=data['training_type'],
            content=content,
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
            raise JournalNotFoundError(journal_id)
        return journal

    async def get_complete_journal(self, journal_id: int) -> Journal | None:
        """Возвращает Journal пользователя."""
        journal = await self.journal_repo.get_complete_journal(journal_id)
        if journal is None:
            raise JournalNotFoundError(journal_id)

        return journal

    async def delete_journals(self, tg_id: int, del_list: Sequence[int]) -> None:
        if not del_list:
            return

        user = await self.user_repo.get_user_by_tg(tg_id, raise_err=True)
        await self.journal_repo.delete_journals(user.id, del_list) # type: ignore
