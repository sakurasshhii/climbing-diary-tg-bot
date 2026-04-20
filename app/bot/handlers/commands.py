from aiogram import Bot, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

commands_router = Router()


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
    await message.answer(text="That's start message!")
