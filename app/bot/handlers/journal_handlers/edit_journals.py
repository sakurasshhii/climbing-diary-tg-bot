"""Module contains handlers of journals' edition menu.

UI:
journals' edition menu:
    add journal
        -> start FSMNewJournal from .add_journal.py
    delete journal -> start FSMDelJournal
        1. select a journal
        2. confirm del
    edit journal -> start FSMEditJournal
        1. select journal
            - edit name
            - edit comment
            - edit workouts
"""

import logging
from collections.abc import Iterable

from aiogram import Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import Message

from app.bot.handlers.journal_handlers.validators import \
    assure_message_from_user_id
from app.bot.keyboards.journal_keyboards import edit_journals_kb
from app.lexic.ru import EDIT_JOURNAL
from app.domain.models import DBJournal
from app.services.services import JournalService

logger = logging.getLogger(__name__)
journal_edit_router = Router()


# ———————————————————————————— open menu kboard —————————————————————————
@journal_edit_router.message(Command("edit_journals"), StateFilter(default_state))
async def process_edit_journal(
    message: Message,
    state: FSMContext,
    journal_service: JournalService
) -> None:
    """Open redacting menu."""
    message, tg_id = assure_message_from_user_id(message)

    await message.answer(
        text=EDIT_JOURNAL["main_menu"],
        reply_markup=edit_journals_kb
    )
