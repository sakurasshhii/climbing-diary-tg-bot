import datetime as dt

from app.infrastructure.database.repo import UserRepository, JournalRepository
from app.domain.models import Journal, Workout, User, ClimbTrain, GymTrain
from app.domain.exceptions import UserNotFoundError
from app.domain.enums import TrainingType, TrainingCategory
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
            journal_repo: JournalRepository) -> None:
        self.user_repo = user_repo
        self.journal_repo = journal_repo

    async def add_journal(self, tg_id: int, comments:str = '') -> None:
        user = await self.user_repo.get_user_by_tg(tg_id)
        if not user:
            raise UserNotFoundError(tg_id)
        await self.journal_repo.add_journal(user_id=user['id'], comments=comments)

    async def add_workout(
            self, tg_id: int, journal_no: int,
            workout_date: dt.date, training_category: str,
            training_type: str, content: str, comments: str) -> None:
        user = await self.user_repo.get_user_by_tg(tg_id)
        if not user:
            raise UserNotFoundError(tg_id)

        workout = JournalParser.parse_workout(
            workout_date=workout_date,
            training_category=TrainingCategory[training_category.upper()],
            training_type=TrainingType[training_type.upper()],
            content=content,
            comments=comments
        )
        await self.journal_repo.add_workout(
            journal_id=journal_no,
            workout=workout
        )

    async def get_workout_by_date(self, date: dt.date) -> Workout | None:
        return await self.journal_repo.get_workout_by_date(date)

    # async def get_journals(self, user_id: int):
    #     ################# to do! 
    #     '''
    #     На доработке:
    #     Сейчас ф-я возвращает номера и комментарии всех существующих журналов пользователя.
    #     '''
    #     return await self.journal_repo.get_journals(user_id=user_id)
    #     return Journal()

    @staticmethod
    def training_sets_validation(text: str, training_cat: str) -> bool:
        return bool(JournalParser.is_valid_rows(text, training_category=training_cat))
