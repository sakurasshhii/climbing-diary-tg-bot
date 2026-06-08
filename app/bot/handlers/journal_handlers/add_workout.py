"""Module contains handlers to add train(workout).

———————————————— FSM schema ————————————————
1. select a journal
    (button: create new / last one / pick from the list)
2.1 add a date
    (button: today / yesterday / other date — write down)
2.2* write a date if other date selected
    (ISOformat: YYYY-MM-DD)
3. add training category
    (button: TRainingCategory — climbing/gym)
4. add training type
    (button: TrainingType — lead/boulder/GPP/SFP)
5. add training content
    (write text: routes / workouts as in the example)
6. add comment
    (write any text)
    >>> FSMWorkoutDataComplete
7. check
    (returns journal workout & update DB if it's ok)
"""

import datetime as dt
import logging
from collections.abc import Iterable
from typing import cast

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from app.bot.handlers import exceptions as exc
from app.bot.handlers.journal_handlers.helpers import (state_add_date_set_next,
                                                       state_pick_j_set_next)
from app.bot.handlers.journal_handlers.validators import (
    assure_callback_message, assure_message_from_user_id)
from app.bot.helper.parser import MessageParser
from app.bot.keyboards.journal_keyboards import (check_kboard, get_journals_kb,
                                                 get_pick_j_kb,
                                                 train_type_kboard)
from app.bot.states.add_workout import (FSMFillWorkout, FSMWorkoutData,
                                        FSMWorkoutDataComplete)
from app.bot.filters.dates_filter import IsCorrectDate
from app.domain.enums import TrainingCategory, TrainingType
from app.domain.models import DBJournal
from app.lexic.ru import FSM_ADD_TRAIN, FSM_ADD_TRAIN_CAT, GET_JOURNAL
from app.services.services import JournalService, UserService

logger = logging.getLogger(__name__)
workout_router = Router()


# ———————————————————————————— FSM —————————————————————————————————————
# ———————————————————————————— 1.journal ———————————————————————————————
@workout_router.message(Command("add_workout"), StateFilter(default_state))
async def process_add_workout_command(
    message: Message,
    state: FSMContext,
    user_service: UserService,
    journal_service: JournalService,
) -> None:
    """Команда /add_workout.

    Выбор журнала: переход к следующему состоянию, добавление клавиатуры.
    Для новых пользователей журнал создается автоматически.
    """

    message = assure_message_from_user_id(message)

    tg_id = message.from_user.id  # type: ignore[union-attr]
    user = await user_service.get_user_assured(tg_id)
    await state.set_state(FSMFillWorkout.select_journal)
    journals = await journal_service.get_journals(tg_id)

    if not user.last_journal and not len(journals):
        await message.answer(FSM_ADD_TRAIN["error_journal_0"])
        await journal_service.add_journal(tg_id)
        user = await user_service.get_user_assured(tg_id)
        logger.info(
            "Добавлен новый журнал для юзера id=%s, journal_id=%s",
            tg_id,
            user.last_journal
        )

        await state_pick_j_set_next(
            user.last_journal, # type: ignore
            state,
            message,
            journal_service,
            user_service,
        )

    else:
        await message.answer(
            text=FSM_ADD_TRAIN["fsm_pick_journal"],
            reply_markup=get_pick_j_kb(
                has_last=bool(user.last_journal),
                has_choice=(len(journals) > 0),
            ),
        )

@workout_router.callback_query(
    StateFilter(FSMFillWorkout.select_journal),
    F.data.in_(["last_journal", "select_journal"]),
)
async def process_pick_journal(
    cback: CallbackQuery,
    state: FSMContext,
    user_service: UserService,
    journal_service: JournalService,
) -> None:
    await cback.answer()
    message = assure_callback_message(cback)
    tg_id = cback.from_user.id # type: ignore

    if cback.data == "select_journal":
            journals: Iterable[DBJournal] = await journal_service.get_journals(tg_id)
            await message.edit_text(
                text=GET_JOURNAL['select_journal'],
                reply_markup=get_journals_kb(journals)
            )

    else:
        user = await user_service.get_user_assured(tg_id)
        await state_pick_j_set_next(
            user.last_journal, # type: ignore
            state,
            message,
            journal_service,
            user_service,
        )

@workout_router.callback_query(
    StateFilter(FSMFillWorkout.select_journal),
    F.data.func(lambda no: no.isdigit())
)
async def process_picked_journal(
    cback: CallbackQuery,
    state: FSMContext,
    journal_service: JournalService,
    user_service: UserService,
) -> None:
    await cback.answer()
    message = assure_callback_message(cback)

    await state_pick_j_set_next(
        int(cback.data), # type: ignore
        state,
        message,
        journal_service,
        user_service
    )

# ———————————————————————————— 2.date ———————————————————————————————
@workout_router.callback_query(
    StateFilter(FSMFillWorkout.add_date),
    F.data.in_(["today", "yesterday"]),
)
async def process_add_date_press(cback: CallbackQuery, state: FSMContext) -> None:
    await cback.answer()
    message = assure_callback_message(cback)

    await message.edit_reply_markup()

    date = dt.datetime.now(tz=dt.UTC).date()
    if cback.data == "yesterday":
        date -= dt.timedelta(days=1)

    await state_add_date_set_next(state=state, date=date, message=message)

@workout_router.callback_query(
    StateFilter(FSMFillWorkout.add_date),
    F.data.in_(["other_date"]),
)
async def process_add_date_press_other(cback: CallbackQuery) -> None:
    await cback.answer()
    message = assure_callback_message(cback)

    await message.edit_reply_markup()

    await message.answer(
        FSM_ADD_TRAIN["fsm_other_date"],
        reply_markup=ReplyKeyboardRemove())

@workout_router.message(
    StateFilter(FSMFillWorkout.add_date),
    IsCorrectDate()) # to do!!! add date filter
async def process_add_date_other(
    message: Message,
    state: FSMContext,
    date: dt.date
) -> None:
    message = assure_message_from_user_id(message)
    await state_add_date_set_next(state=state, date=date, message=message)

@workout_router.message(
        StateFilter(FSMFillWorkout.add_date),
        F.text)
async def process_add_date_other_error(
        message: Message) -> None:

    message = assure_message_from_user_id(message)
    await message.answer(FSM_ADD_TRAIN["error_invalid_date"])

# ———————————————————————————— 3.category ———————————————————————————————
@workout_router.callback_query(
    StateFilter(FSMFillWorkout.add_train_type),
    F.data.in_(["climbing", "gym"]),
)
async def process_add_train_cat(cback: CallbackQuery, state: FSMContext) -> None:
    """Step 3. Add the training type."""
    await cback.answer()
    message = assure_callback_message(cback)

    try:
        cback_data = cback.data or ""
        training_cat = TrainingCategory[cback_data.upper()]
    except KeyError:
        logger.exception(f"Invalid TrainigCategory from cback: {cback.data}")
        raise

    await state.update_data(training_category=training_cat)
    await message.edit_reply_markup(reply_markup=train_type_kboard[training_cat])

# ———————————————————————————— 4.type ———————————————————————————————
@workout_router.callback_query(
    StateFilter(FSMFillWorkout.add_train_type),
    F.data.in_(["boulder", "lead", "SFP", "GPP"]),
)
async def process_add_train_type(cback: CallbackQuery, state: FSMContext) -> None:
    await cback.answer()
    message = assure_callback_message(cback)

    await message.edit_reply_markup()

    cback_data: str = cback.data or ""
    await state.update_data(training_type=TrainingType[cback_data.upper()])
    data: FSMWorkoutData = cast("FSMWorkoutData", await state.get_data())

    training_cat: TrainingCategory = data.get("training_category", None)
    if training_cat is None:
        raise exc.JournalError(text="TrainingCategory missed in FSM data")

    await state.set_state(FSMFillWorkout.add_train_content)
    await message.answer(FSM_ADD_TRAIN_CAT[training_cat]["fsm_add_content"])

# ———————————————————————————— 5.content ———————————————————————————————
@workout_router.message(StateFilter(FSMFillWorkout.add_train_content), F.text)
async def process_add_train_content(message: Message, state: FSMContext) -> None:
    """Step 4. Add training content."""
    message = assure_message_from_user_id(message)

    data: FSMWorkoutData = cast("FSMWorkoutData", await state.get_data())
    training_cat: TrainingCategory = data.get("training_category", None)

    if training_cat is None:
        raise exc.JournalError(text="TrainingCategory missed in FSM data")

    is_valid = JournalService.training_sets_validation(
        text=message.text or "",
        training_cat=training_cat,
    )
    if not is_valid:
        await message.answer(FSM_ADD_TRAIN["error_invalid_sets"])
        return

    await state.update_data(content=message.text)
    await state.set_state(FSMFillWorkout.add_comment)

    await message.answer(FSM_ADD_TRAIN["fsm_add_comment"])

# ———————————————————————————— 6.comment ———————————————————————————————
@workout_router.message(StateFilter(FSMFillWorkout.add_comment), F.text)
async def process_add_train_comment(message: Message, state: FSMContext) -> None:
    """Step 5. Add comment to the train."""
    await state.update_data(comments=message.text)
    await state.set_state(FSMFillWorkout.check)
    data: FSMWorkoutDataComplete = cast(
        "FSMWorkoutDataComplete",
        await state.get_data(),
    )

    workout = MessageParser.prettify_FSM_workout_data(data)
    await message.answer(
        text=FSM_ADD_TRAIN["fsm_to_check"].format(workout),
        reply_markup=check_kboard)

# ———————————————————————————— 7.check ———————————————————————————————
@workout_router.callback_query(
    StateFilter(FSMFillWorkout.check),
    F.data.in_(["correct"]),
)
async def process_check_correct(
    cback: CallbackQuery,
    state: FSMContext,
    journal_service: JournalService,
) -> None:
    """Step 6. Check & push into DB."""
    await cback.answer()
    message = assure_callback_message(cback)

    await message.edit_reply_markup()

    tg_id = cback.from_user.id
    data: FSMWorkoutDataComplete = cast(
        "FSMWorkoutDataComplete",
        await state.get_data(),
    )

    ############## to do!
    # Исправить на добавление train: на случай, если это вторая тренировка за день
    await journal_service.add_workout(tg_id, data)
    await message.answer(
        text=FSM_ADD_TRAIN["fsm_complete"],
        reply_markup=ReplyKeyboardRemove())
    await state.clear()

    logger.info(f"Собранная информация state.get_data(): {data}")

@workout_router.callback_query(
    StateFilter(FSMFillWorkout.check),
    F.data.in_(["incorrect"]),
)
async def process_check_incorrect(cback: CallbackQuery, state: FSMContext) -> None:
    ########### to do! добавить редактирование данных
    await cback.answer()
    message = assure_callback_message(cback)

    await message.edit_reply_markup()

    await state.clear()
    await message.answer(
        text=FSM_ADD_TRAIN["fsm_check_incorrect"],
        reply_markup=ReplyKeyboardRemove(),
    )
