"""Add new journal to DB.

———————————————— FSM schema ————————————————
1. input name (2 < len < 16)
2. input comments (or '-' for no comments)
    >>> FSMNewJournalComplete
"""

import datetime as dt
import logging
from typing import cast
from collections.abc import Iterable

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from app.bot.handlers.journal_handlers.validators import (
    assure_callback_message, assure_message_from_user_id)
from app.bot.handlers.journal_handlers.helpers import state_pick_j_set_next, state_add_date_set_next
from app.bot.helper.parser import MessageParser
from app.bot.keyboards.journal_keyboards import (
    check_kboard, date_kboard, train_cat_kboard, train_type_kboard,
    get_pick_j_kb, get_journals_kb)
from app.bot.states.add_workout import (FSMFillWorkout, FSMWorkoutData,
                                        FSMWorkoutDataComplete)
from app.bot.states.edit_journal import FSMNewJournal, FSMNewJournalComplete
from app.domain.enums import TrainingCategory, TrainingType
from app.domain.models import User, DBJournal
from app.lexic.ru import FSM_ADD_TRAIN, FSM_ADD_TRAIN_CAT, CHECK_JOURNAL
from app.services.services import JournalService, UserService


logger = logging.getLogger(__name__)
journal_add_router = Router()


# ———————————————————————————— 1. add name ——————————————————————————————————
@journal_add_router.callback_query(
    StateFilter(FSMFillWorkout.select_journal),
    F.data.in_(["new_journal"]),
)
async def process_j_input_name(
    cback: CallbackQuery,
    state: FSMContext,
) -> None:
    await cback.answer()
    message = assure_callback_message(cback)

    await state.set_state(FSMNewJournal.input_name)
    await message.answer(text="Введите название журнала тренировок 2 < символов < 16.")

@journal_add_router.message(
    StateFilter(FSMNewJournal.input_name),
    F.text,
)
async def process_j_name(
    message: Message,
    state: FSMContext,
) -> None:
    message = assure_message_from_user_id(message)
    name = message.text if message.text else ""

    if len(name) > 15:
        await message.answer(text=f"Слишком длинное название. Сократите до 15 символов: {name[:15] + "."}")
    elif len(name) < 2:
        await message.answer(text="Название журнала должно иметь длину от 2 до 15 символов.")
    else:
        await state.update_data(journal_name=name)
        await state.set_state(FSMNewJournal.input_comment)
        await message.answer(text=f"Название журнала: {name}. Укажите комментарии или впишите прочерк...")

@journal_add_router.message(
    StateFilter(FSMNewJournal.input_comment),
    F.text,
)
async def process_j_comments(
    message: Message,
    state: FSMContext,
    journal_service: JournalService,
    user_service: UserService,
) -> None:
    message = assure_message_from_user_id(message)

    comments = message.text if message.text else ""
    await state.update_data(journal_comments=comments)

    tg_id = message.from_user.id # type: ignore

    data: FSMNewJournalComplete = cast(
        "FSMNewJournalComplete",
        await state.get_data(),
    )

    await journal_service.add_journal(tg_id, data["journal_name"], data["journal_comments"])
    user = await user_service.get_user_assured(tg_id)
    logger.info(f"Добавлен новый журнал для юзера id={user}")

    await state_pick_j_set_next(
        user.last_journal,
        state=state,
        message=message,
        journal_service=journal_service,
        user_service=user_service,
    )
