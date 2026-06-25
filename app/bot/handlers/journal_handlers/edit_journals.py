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

from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import Message, CallbackQuery

from app.bot.handlers.journal_handlers.validators import \
    assure_message_from_user_id, assure_callback_message
from app.bot.handlers.journal_handlers.helpers import state_add_journal_start
from app.bot.keyboards.journal_keyboards import edit_journals_kb
from app.bot.states.edit_journal import (FSMDeleteJournal, FSMEditJournal,
                                         FSMAddJournal, FSMUserMenu)
from app.lexic.ru import EDIT_JOURNAL
from app.services.services import JournalService

logger = logging.getLogger(__name__)
journal_edit_router = Router()


# ———————————————————————————— open menu kboard —————————————————————————
@journal_edit_router.message(Command("edit_journals"), StateFilter(default_state))
async def process_journal_menu(message: Message, state: FSMContext) -> None:
    """Open journals' redacting menu."""
    message, _ = assure_message_from_user_id(message)
    await state.set_state(FSMUserMenu.journal_menu)

    await message.answer(
        text=EDIT_JOURNAL["main_menu"],
        reply_markup=edit_journals_kb
    )

# ———————————————————————————— edit journal —————————————————————————
@journal_edit_router.callback_query(
    StateFilter(FSMUserMenu.journal_menu),
    F.data.in_(["edit_journal"]),)
async def process_edit_journal(
    cback: CallbackQuery,
    state: FSMContext,
) -> None:
    await cback.answer()
    message = assure_callback_message(cback)

    await message.answer(
        text="Button pressed: edit_journal"
    )

    await state.set_state(FSMEditJournal.select_journal)

# ———————————————————————————— add_journal —————————————————————————
@journal_edit_router.callback_query(
    StateFilter(FSMUserMenu.journal_menu),
    F.data.in_(["add_journal"]),)
async def process_add_journal(
    cback: CallbackQuery,
    state: FSMContext,
) -> None:
    await cback.answer()
    message = assure_callback_message(cback)

    await message.answer(
        text="Button pressed: select_journal"
    )

    await state_add_journal_start(message, state)

# ———————————————————————————— delete_journal —————————————————————————
@journal_edit_router.callback_query(
    StateFilter(FSMUserMenu.journal_menu),
    F.data.in_(["delete_journal"]),)
async def process_delete_journal(
    cback: CallbackQuery,
    state: FSMContext,
) -> None:
    await cback.answer()
    message = assure_callback_message(cback)

    await message.answer(
        text="Button pressed: delete_journal"
    )

    await state.set_state(FSMDeleteJournal.select_journal)
