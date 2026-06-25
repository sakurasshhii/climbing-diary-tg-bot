"""Add new journal to DB.

———————————————— FSM schema ————————————————
1. input name (2 < len < 16)
2. input comments (or '-' for no comments)
    >>> FSMNewJournalComplete
"""

import logging
from typing import cast

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.handlers.journal_handlers.helpers import state_pick_j_set_next
from app.bot.handlers.journal_handlers.validators import (
    assure_callback_message, assure_message_from_user_id)
from app.bot.states.add_workout import FSMFillWorkout
from app.bot.states.edit_journal import FSMNewJournal, FSMNewJournalComplete
from app.lexic.ru import ADD_JOURNAL
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
    await message.answer(text=ADD_JOURNAL["input_name"])

@journal_add_router.message(
    StateFilter(FSMNewJournal.input_name),
    F.text,
)
async def process_j_name(
    message: Message,
    state: FSMContext,
) -> None:
    message, _ = assure_message_from_user_id(message)
    name = message.text if message.text else ""

    if len(name) > 15:
        await message.answer(text=ADD_JOURNAL["name_too_long"].format(name[:15] + "."))
    elif len(name) < 2:
        await message.answer(text=ADD_JOURNAL["name_too_short"])
    else:
        await state.update_data(journal_name=name)
        await state.set_state(FSMNewJournal.input_comment)
        await message.answer(text=ADD_JOURNAL["input_comments"].format(name))

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
    message, tg_id = assure_message_from_user_id(message)

    comments = message.text if message.text else ""
    await state.update_data(journal_comments=comments)

    data: FSMNewJournalComplete = cast(
        "FSMNewJournalComplete",
        await state.get_data(),
    )

    await journal_service.add_journal(tg_id, data["journal_name"], data["journal_comments"])
    await message.answer(text=ADD_JOURNAL["completed"].format(data["journal_name"], data["journal_comments"]))
    user = await user_service.get_user_assured(tg_id)
    logger.info(f"Добавлен новый журнал для юзера id={user}")

    await state_pick_j_set_next(
        user.last_journal, # type: ignore
        state=state,
        message=message,
        journal_service=journal_service,
        user_service=user_service,
    )
