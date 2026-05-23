import logging
import datetime as dt

from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from typing import cast

from app.bot.handlers.journal_handlers.validators import assure_message_from_user_id, assure_callback_message
from app.bot.states.fsm import FSMFillWorkout, FSMWorkoutData, FSMWorkoutDataComplete
from app.services.services import UserService, JournalService
from app.domain.enums import TrainingType, TrainingCategory
from app.bot.handlers import exceptions as exc
from app.bot.keyboards.journal_keyboards import (
    date_kboard, train_type_kboard, wrk_write_kboard,
    gym_train_kboard, climb_train_kboard
)
from app.lexic.ru import JOURNAL, MAIN_MENU_MSG

logger = logging.getLogger(__name__)
journal_router = Router()


############################# get from DB ####################################

@journal_router.message(Command('my_journals'))
async def process_my_journals(
    message: Message,
    journal_service: JournalService
) -> None:
    '''
    Showing user's journals from DB
    '''
    message = assure_message_from_user_id(message)
    tg_id = message.from_user.id # type: ignore
    journals = await journal_service.get_journals(tg_id)
    await message.answer(
        text='\n'.join(str(j) for j in journals)
    )