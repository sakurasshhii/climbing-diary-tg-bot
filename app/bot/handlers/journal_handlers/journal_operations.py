"""
Get information from DB.

/my_journal — get & show user's journal.
1. select a journal
2. print / send file
"""
import logging
from collections.abc import Iterable

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove, BufferedInputFile

from app.bot.handlers import exceptions as exc
from app.bot.handlers.journal_handlers.validators import (
    assure_callback_message, assure_message_from_user_id)
from app.bot.keyboards.journal_keyboards import get_journals_kb
from app.bot.states.get_journal import FSMGetJournal
from app.domain.enums import TrainingCategory, TrainingType
from app.domain.models import DBJournal, Journal
from app.lexic.ru import CHECK_JOURNAL
from app.services.services import JournalService, UserService

logger = logging.getLogger(__name__)
journal_router = Router()


# ———————————————————————————— helper ————————————————————————————————————

# ———————————————————————————— FSM ———————————————————————————————————————
# ———————————————————————————— 1.select ——————————————————————————————————

@journal_router.message(Command('my_journal'), StateFilter(default_state))
async def process_my_journal(
    message: Message,
    state: FSMContext,
    journal_service: JournalService
) -> None:
    """Select from user's journals."""
    message = assure_message_from_user_id(message)

    tg_id = message.from_user.id # type: ignore
    journals: Iterable[DBJournal] = await journal_service.get_journals(tg_id)

    await state.set_state(FSMGetJournal.select_journal)
    await message.answer(
        text=CHECK_JOURNAL['select_journal'],
        reply_markup=get_journals_kb(journals)
    )

# ———————————————————————————— 2.send ——————————————————————————————————
@journal_router.callback_query(StateFilter(FSMGetJournal.select_journal))
async def process_show_journal(
    cback: CallbackQuery,
    state: FSMContext,
    journal_service: JournalService
) -> None:
    await cback.answer()
    await state.clear()
    message = assure_callback_message(cback)

    if cback.data is None:
        raise ValueError

    journal: Journal | None = await journal_service.get_complete_journal(int(cback.data))

    if journal is None:
        await message.answer(text="NOT FOUND")
        return

    await message.answer(
        text="JOURNAL IN TXT DOC —>",
        reply_markup=ReplyKeyboardRemove()
    )
    await message.answer_document(
        document=BufferedInputFile(
            file=str(journal).encode("utf-8"),
            filename="my_journal.txt"
        )
    )
