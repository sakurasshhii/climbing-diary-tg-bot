import logging

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from app.lexic.ru import MAIN_MENU_MSG, JOURNAL
from app.infrastructure.database import UserRepository

logger = logging.getLogger(__name__)
commands_router = Router()


# /start
@commands_router.message(CommandStart())
async def process_start_command(
    message: Message,
    user_repo: UserRepository
) -> None:
    if message.from_user:
        await user_repo.add_user(
            message.from_user.id,
            message.from_user.username
        )
    await message.answer(text=MAIN_MENU_MSG['/start'])

# /help
@commands_router.message(Command(commands=['help']))
async def process_help_command(
    message: Message,
    user_repo: UserRepository
) -> None:
    if message.from_user:
        user_info = await user_repo.get_user(message.from_user.id) or []
        logger.info(f'Получена информация из БД:\n{dict(user_info)}')
    await message.answer(MAIN_MENU_MSG['/help'])

# /add_workout
@commands_router.message(Command(commands=['add_workout']))
async def process_add_workout_command(
    message: Message,
    user_repo: UserRepository
) -> None:
    if message.from_user:
        user_id = message.from_user.id
        user = await user_repo.get_user_assured(user_id)
        journal_no = user['last_journal']

        if journal_no == 0:
            await message.answer(text=JOURNAL['errors_journal_0'])
            await message.answer(text=JOURNAL['about_journal'])
            await user_repo.add_journal(user_id)

            added_j = await user_repo.get_journal(user_id) or []
            logger.info(f'Добавлен журнал для юзера id={user_id}: {[dict(j) for j in added_j]}')