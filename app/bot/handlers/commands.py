import logging

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from app.lexic.ru import MAIN_MENU_MSG, JOURNAL
from app.services.services import UserService

logger = logging.getLogger(__name__)
commands_router = Router()
undefined_router = Router()


# /start
@commands_router.message(CommandStart())
async def process_start_command(
    message: Message,
    user_service: UserService
) -> None:
    if message.from_user:
        await user_service.add_user(
            message.from_user.id,
            message.from_user.username
        )
    await message.answer(text=MAIN_MENU_MSG['/start'])

# /help
@commands_router.message(Command(commands=['help']))
async def process_help_command(
    message: Message,
    user_service: UserService
) -> None:
    if message.from_user:
        user = await user_service.get_user_assured(message.from_user.id)
        logger.info(f'Получена информация из БД:\n{user}')
    await message.answer(MAIN_MENU_MSG['/help'])

# undefined messages
@undefined_router.message()
async def undefined_message(
    message: Message
) -> None:
    await message.answer(text='undefined message!')
    logger.warning(f'Undefined message: {message.text}')

@undefined_router.callback_query()
async def undefined_cback(
    cback: CallbackQuery,
    state: FSMContext
) -> None:
    user_state = await state.get_state()
    await cback.answer(text='undefined callback!')
    logger.warning(f'Undefined callback: {cback.data}; state: {user_state}')