import datetime as dt
import logging

from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from app.bot.keyboards.journal_keyboards import select_date_kb, train_cat_kb
from app.bot.states.add_workout import FSMFillWorkout
from app.bot.states.edit_journal import FSMAddJournal
from app.lexic.ru import ADD_JOURNAL, FSM_ADD_TRAIN
from app.services.services import JournalService

logger = logging.getLogger(__name__)


async def state_pick_j_set_next(
    journal_id: int,
    state: FSMContext,
    message: Message,
    journal_service: JournalService,
) -> None:
    """FSM process template.

    Get journal id from user -> process -> set next state (date).
    """
    await state.update_data(journal_no=journal_id)
    await state.set_state(FSMFillWorkout.add_date)

    journal = await journal_service.get_journal(journal_id)
    text = "\n\n".join((
        FSM_ADD_TRAIN["chosen_journal"].format(journal.preview),
        FSM_ADD_TRAIN["fsm_add_date"],
    ))

    await message.answer(
        text=text,
        reply_markup=select_date_kb,
    )

async def state_add_date_set_next(
    date: dt.date,
    state: FSMContext,
    message: Message,
    journal_service: JournalService,
) -> None:
    """FSM process template.

    Get workout date from user -> process -> set next state (train_type).
    """
    data = await state.get_data()
    journal_id = data.get("journal_id")
    if journal_id is None:
        raise RuntimeError("journal_id not found in FSM")

    workout_exists = await journal_service.check_workout_in_journal(date, journal_id)
    if workout_exists:
        await message.answer(
            text="ТРЕНИРОВКА В ЭТОТ ДЕНЬ УЖЕ ЗАПИСАНА",
            reply_markup=ReplyKeyboardRemove(),
        )
        await state.clear()
        return

    await state.update_data(workout_date=date)
    await state.set_state(FSMFillWorkout.add_train_type)
    await message.answer(
        text=FSM_ADD_TRAIN["fsm_add_train_type"],
        reply_markup=train_cat_kb,
    )

async def state_add_journal_start(
    message: Message,
    state: FSMContext,
) -> None:
    """FSM process template.

    Edit journals & add_journal — start FSM (AddJournal).
    """
    await state.set_state(FSMAddJournal.input_name)
    await message.answer(text=ADD_JOURNAL["input_name"])
