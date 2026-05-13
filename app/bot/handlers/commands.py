import logging

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from app.lexic.ru import MAIN_MENU_MSG
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
        user_info = await user_repo.get_user(message.from_user.id)
        logger.info(f'Получена информация из БД:\n{user_info}')
    await message.answer(MAIN_MENU_MSG['/help'])