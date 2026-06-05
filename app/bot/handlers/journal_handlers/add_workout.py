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
7. check
    (returns journal workout & update DB if it's ok)
"""
import datetime as dt
import logging
from typing import cast

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from app.bot.handlers import exceptions as exc
from app.bot.handlers.journal_handlers.validators import (
    assure_callback_message, assure_message_from_user_id)
from app.bot.helper.parser import MessageParser
from app.bot.keyboards.journal_keyboards import (check_kboard, date_kboard,
                                                 train_cat_kboard,
                                                 train_type_kboard)
from app.bot.states.add_workout import (FSMFillWorkout, FSMWorkoutData,
                                        FSMWorkoutDataComplete)
from app.domain.enums import TrainingCategory, TrainingType
from app.lexic.ru import FSM_ADD_TRAIN, FSM_ADD_TRAIN_CAT
from app.services.services import JournalService, UserService

logger = logging.getLogger(__name__)
workout_router = Router()


# ———————————————————————————— helper ——————————————————————————————————
async def set_date_state(
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

# ———————————————————————————— FSM —————————————————————————————————————
# ———————————————————————————— 1.journal ———————————————————————————————
# to do!!!!!!!: добавить выбор журнала перед записью тренировки
@workout_router.message(Command("add_workout"), StateFilter(default_state))
async def process_add_workout_command(
    message: Message,
    state: FSMContext,
    user_service: UserService,
    journal_service: JournalService,
) -> None:
    """Add workout in last edited journal.

    The last one journal will be selected by default.
    If there are no journal — it creates automatically.
    """
    message = assure_message_from_user_id(message)

    user_id = message.from_user.id  # type: ignore[union-attr]
    user = await user_service.get_user_assured(user_id)

    if user.last_journal == 0:
        await message.answer(FSM_ADD_TRAIN["error_journal_0"])
        await journal_service.add_journal(user_id)
        logger.info(f"Добавлен новый журнал для юзера id={user_id}")
        user = await user_service.get_user_assured(user_id)

    journal = await journal_service.get_journal(user.last_journal)
    text = FSM_ADD_TRAIN["fsm_add_date"] + "\n\n" + \
        FSM_ADD_TRAIN["chosen_journal"].format(journal.preview)

    await state.update_data(journal_no=user.last_journal)
    await state.set_state(FSMFillWorkout.add_date)
    await message.answer(
        text=text,
        reply_markup=date_kboard,
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

    await set_date_state(state=state, date=date, message=message)

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
    F.text.regexp(r"^\d{4}-\d{2}-\d{2}$")) # to do!!! add date filter
async def process_add_date_other(message: Message, state: FSMContext) -> None:
    message = assure_message_from_user_id(message)

    try:
        date = dt.date.fromisoformat(message.text or "")
    except ValueError:
        await message.answer(FSM_ADD_TRAIN["error_invalid_date"])
    else:
        await set_date_state(state=state, date=date, message=message)

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
        text=FSM_ADD_TRAIN["fsm_to_check"].format(workout), ########################
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
