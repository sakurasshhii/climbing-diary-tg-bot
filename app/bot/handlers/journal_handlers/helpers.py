import datetime as dt
import logging

from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.keyboards.journal_keyboards import (date_kboard, train_cat_kboard)
from app.bot.states.add_workout import FSMFillWorkout
from app.lexic.ru import FSM_ADD_TRAIN
from app.services.services import JournalService, UserService

logger = logging.getLogger(__name__)


# ———————————————————————————— helper ——————————————————————————————————
async def state_add_date_set_next(
    date: dt.date,
    state: FSMContext,
    message: Message,
) -> None:
    await state.update_data(workout_date=date)
    await state.set_state(FSMFillWorkout.add_train_type)
    await message.answer(
        text=FSM_ADD_TRAIN["fsm_add_train_type"],
        reply_markup=train_cat_kboard,
    )

async def state_pick_j_set_next(
    tg_id: int,
    state: FSMContext,
    message: Message,
    journal_service: JournalService,
    user_service: UserService,
) -> None:
    user = await user_service.get_user_assured(tg_id)
    journal = await journal_service.get_journal(user.last_journal)

    await state.update_data(journal_no=user.last_journal)
    await state.set_state(FSMFillWorkout.add_date)

    text = FSM_ADD_TRAIN["chosen_journal"].format(journal.preview) + "\n\n" + \
        FSM_ADD_TRAIN["fsm_add_date"]
    await message.answer(
        text=text,
        reply_markup=date_kboard,
    )
