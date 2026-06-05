"""Module contains handlers to process main menu commands."""
import logging

from aiogram import Router
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from app.lexic.ru import MAIN_MENU_MSG, UNDEFINED
from app.services.services import UserService

logger = logging.getLogger(__name__)

commands_router = Router()
undefined_router = Router()


@commands_router.message(CommandStart())
async def process_start_command(message: Message, user_service: UserService) -> None:
    """/start."""
    if message.from_user:
        await user_service.add_user(
            message.from_user.id,
            message.from_user.username,
        )
    else:
        raise ValueError("No user info!")

    # users = await user_service.get_all_users()
    # logger.info("CURRENT USERS: %s", users)
    await message.answer(text=MAIN_MENU_MSG["/start"])

@commands_router.message(Command(commands=["help"]))
async def process_help_command(message: Message, user_service: UserService) -> None:
    """/help."""
    if message.from_user:
        user = await user_service.get_user_assured(message.from_user.id)
        logger.info("Получена информация из БД: %s", user)
    await message.answer(MAIN_MENU_MSG["/help"])

@commands_router.message(Command("cancel"), ~StateFilter(default_state))
async def process_cancel_command(message: Message, state: FSMContext) -> None:
    """/cancel — use to escape any FSM process."""
    user_state = await state.get_state()
    logger.info("Пользователь прервал операцию на состоянии=%s", user_state)
    await state.clear()
    await message.answer(
        MAIN_MENU_MSG["/cancel"],
        reply_markup=ReplyKeyboardRemove(),
    )

@undefined_router.message()
async def undefined_message(message: Message) -> None:
    """Any undefined messages from user."""
    await message.answer(text=UNDEFINED["message"])
    logger.warning("Undefined message=%s", message.text)

@undefined_router.callback_query()
async def undefined_cback(cback: CallbackQuery, state: FSMContext) -> None:
    """Any undefined callback."""
    user_state = await state.get_state()
    if cback.message:
        await cback.message.answer(text=UNDEFINED["callback"])
    logger.warning("Undefined callback=%s; state=%s", cback.data, user_state)
