from aiogram import Bot, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from app.lexic.ru import MAIN_MENU_MSG

commands_router = Router()


# /start
@commands_router.message(CommandStart())
async def process_start_command(
    message: Message,
    users
) -> None:
    if message.from_user:
        await users.add_user(
            message.from_user.id,
            message.from_user.username
        )
    await message.answer(text=MAIN_MENU_MSG['/start'])

# /help
@commands_router.message(Command(commands=['help']))
async def process_help_command(message: Message):
    await message.answer(MAIN_MENU_MSG['/help'])