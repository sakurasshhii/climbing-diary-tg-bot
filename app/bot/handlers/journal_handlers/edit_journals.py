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
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove

from app.bot.handlers.journal_handlers.validators import \
    assure_message_from_user_id, assure_callback_message
from app.bot.handlers.journal_handlers.helpers import state_add_journal_start
from app.bot.filters.handler_filters import IsDigit
from app.bot.keyboards.journal_keyboards import edit_journals_kb, build_del_journal_kb, confirm_del_kb
from app.bot.states.edit_journal import FSMDeleteJournal, FSMEditJournal, FSMUserMenu
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

    logger.info("BUTTON PRESSED: edit_journal")

    await message.edit_text(
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

    logger.info("BUTTON PRESSED: select_journal")

    await message.delete()
    await state_add_journal_start(message, state)

# ———————————————————————————— delete_journal —————————————————————————
@journal_edit_router.callback_query(
    StateFilter(FSMUserMenu.journal_menu),
    F.data.in_(["delete_journal"]),
)
async def process_delete_journal(
    cback: CallbackQuery,
    state: FSMContext,
    journal_service: JournalService,
) -> None:
    await cback.answer()
    message = assure_callback_message(cback)
    journals = await journal_service.get_journals(cback.from_user.id)

    logger.info("BUTTON PRESSED: delete_journal")

    await message.edit_text(
        text=EDIT_JOURNAL["del_select"],
        reply_markup=build_del_journal_kb(journals, col_optimization=True)
    )

    await state.set_state(FSMDeleteJournal.select_journal)

@journal_edit_router.callback_query(
    StateFilter(FSMDeleteJournal.select_journal),
    IsDigit(),
)
async def process_select_to_del(
    cback: CallbackQuery,
    state: FSMContext,
    journal_service: JournalService,
) -> None:
    await cback.answer()
    state_data = await state.get_data()
    message = assure_callback_message(cback)

    del_list = state_data.get("del_list", [])
    del_list.append(cback.data)
    await state.update_data(del_list=del_list)

    journals = await journal_service.get_journals(cback.from_user.id)
    new_kb = build_del_journal_kb(journals, col_optimization=True, del_list={int(x) for x in del_list})

    await message.edit_reply_markup(
        reply_markup=new_kb,
    )

    # TODO переделать в хэлпер, чтобы можно было вызывать повторно
    # (когда нажали ок но не выбрали ничего из списка)

@journal_edit_router.callback_query(
    StateFilter(FSMDeleteJournal.select_journal),
    F.data.in_(["ok"])
)
async def process_delete_confirm(
    cback: CallbackQuery,
    state: FSMContext,
    journal_service: JournalService,
) -> None:
    message = assure_callback_message(cback)
    state_data = await state.get_data()
    del_list = state_data.get("del_list", [])
    if not del_list:
        await cback.answer(
            text="NO SELECTED JOURNALS",
        )
        return

    await cback.answer()

    journals = await journal_service.get_journals_by_ids(del_list)
    journals = "\n".join(j.preview for j in journals)

    logger.info("STATE data: %s", state_data)
    logger.info("SELECTED journals: %s", journals)

    await message.edit_text(
        text=EDIT_JOURNAL["del_confirm"].format(journals),
        reply_markup=confirm_del_kb
    )   

    await state.set_state(FSMDeleteJournal.confirm_del)

@journal_edit_router.callback_query(
    StateFilter(FSMDeleteJournal.confirm_del)
)
async def process_delete_finish(
    cback: CallbackQuery,
    state: FSMContext,
    journal_service: JournalService,
) -> None:
    await cback.answer()
    message = assure_callback_message(cback)
    state_data = await state.get_data()
    del_list = state_data.get("del_list", [])

    if cback.data == "cancel":
        await message.edit_text(text="УДАЛЕНИЕ ОТМЕНЕНО")
    else:
        await journal_service.delete_journals(cback.from_user.id, del_list)
        await message.edit_text(text="УДАЛЕНИЕ ЗАВЕРШЕНО")

    await state.clear()

    # ВЕРНУТЬСЯ В МЕНЮ
