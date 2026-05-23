'''
Module contains handlers to manage journal.

-- UI & FSM schema --
(journal / Workout creation)

1. select a journal
    (button: create new / last one / pick from the list)
2.1 add a date
    (button: today / yesterday / other date — write down)
2.2* write a date if other date selected
    (ISOformat: YYYY-MM-DD)
3. add training type
    (button: ClimbTrain / GymTrain <class Train>)
4. add training content
    (write text: routes / workouts as in the example)
5. add comment
    (write any text)
6. check
    (returns journal workout & update DB if it's ok)
'''
import logging
import datetime as dt

from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from typing import cast

from app.bot.handlers.journal_handlers.validators import assure_message_from_user_id, assure_callback_message
from app.bot.states.fsm import FSMFillWorkout, FSMWorkoutData, FSMWorkoutDataComplete
from app.services.services import UserService, JournalService
from app.domain.enums import TrainingType, TrainingCategory
from app.bot.handlers import exceptions as exc
from app.lexic.ru import JOURNAL
from app.bot.keyboards.journal_keyboards import (
    date_kboard, train_type_kboard, wrk_write_kboard,
    gym_train_kboard, climb_train_kboard
)

logger = logging.getLogger(__name__)
workout_router = Router()


########################## functions ##########################################

async def set_date_state(
        date: dt.date,
        state: FSMContext,
        message: Message
) -> None:
    await state.update_data(workout_date=date)
    await state.set_state(FSMFillWorkout.add_train_type)
    await message.answer(
        text=JOURNAL['fsm_add_train_type'],
        reply_markup=train_type_kboard
    )

############################# fill form ######################################
'''
/add_workout
Start FSM process of colleting workout data & update database.
'''
@workout_router.message(Command('add_workout'), StateFilter(default_state))
async def process_add_workout_command(
        message: Message, state: FSMContext,
        user_service: UserService,
        journal_service: JournalService) -> None:
    '''
    Default way to add workout.
    The last one journal will be selected by default.
    If there are no journal — it creates automatically.
    '''
    message = assure_message_from_user_id(message)

    user_id = message.from_user.id # type: ignore
    user = await user_service.get_user_assured(user_id)

    if user.last_journal == 0:
        await message.answer(text=JOURNAL['error_journal_0'])
        await journal_service.add_journal(user_id)
        logger.info(f'Добавлен новый журнал для юзера id={user_id}')
        user = await user_service.get_user_assured(user_id)

    await state.update_data(journal_no=int(user.last_journal))
    await state.set_state(FSMFillWorkout.add_date)
    await message.answer(
        text=JOURNAL['fsm_add_date'],
        reply_markup=date_kboard)

    # log
    data: FSMWorkoutData = cast(FSMWorkoutData, await state.get_data())
    logger.info(f'FSM state changed. state.data: {data}')

############################# add a date #####################################

@workout_router.callback_query(
        StateFilter(FSMFillWorkout.add_date),
        F.data.in_(['today', 'yesterday']))
async def process_add_date_press(
        cback: CallbackQuery, state: FSMContext) -> None:

    await cback.answer()
    message = assure_callback_message(cback)

    if cback.data == 'today':
        date = dt.date.today()
    else:
        date = dt.date.today() - dt.timedelta(days=1)

    await set_date_state(state=state, date=date, message=message)

@workout_router.callback_query(
        StateFilter(FSMFillWorkout.add_date),
        F.data.in_(['other_date']))
async def process_add_date_press_other(
        cback: CallbackQuery, state: FSMContext) -> None:

    await cback.answer()
    message = assure_callback_message(cback)

    await message.answer(
        JOURNAL['fsm_other_date'],
        reply_markup=ReplyKeyboardRemove())

@workout_router.message(
        StateFilter(FSMFillWorkout.add_date),
        F.text.regexp(r'^\d{4}-\d{2}-\d{2}$'))               # add date filter
async def process_add_date_other(
        message: Message, state: FSMContext) -> None:

    message = assure_message_from_user_id(message)

    try:
        date = dt.date.fromisoformat(message.text or '')
    except ValueError as e:
        await message.answer(JOURNAL['error_invalid_date'])
    else:
        await set_date_state(state=state, date=date, message=message)

@workout_router.message(
        StateFilter(FSMFillWorkout.add_date),
        F.text)
async def process_add_date_other_error(
        message: Message) -> None:

    message = assure_message_from_user_id(message)
    await message.answer(JOURNAL['error_invalid_date'])

############################# add training type ########################

@workout_router.callback_query(
        StateFilter(FSMFillWorkout.add_train_type),
        F.data.in_(['climbing', 'gym']))
async def process_add_train_type(
        cback: CallbackQuery, state: FSMContext) -> None:
    '''
    Step 3. Add the training type.
    '''
    await cback.answer()
    message = assure_callback_message(cback)
    cback_data = cback.data or ''
    await state.update_data(training_category=TrainingCategory[cback_data.upper()])

    match cback.data:
        case 'climbing':
            await message.edit_reply_markup(reply_markup=climb_train_kboard)
        case 'gym':
            await message.edit_reply_markup(reply_markup=gym_train_kboard)
        case _:
            raise exc.JournalError(
                f'Trainig category [cback] not founded: {cback.data}'
            )

@workout_router.callback_query(
    StateFilter(FSMFillWorkout.add_train_type),
    F.data.in_(['boulder', 'lead', 'SFP', 'GPP']))
async def process_add_train_subtype(
    cback: CallbackQuery, state: FSMContext) -> None:

    await cback.answer()
    message = assure_callback_message(cback)

    cback_data = cback.data or ''
    await state.update_data(training_type=TrainingType[cback_data.upper()])
    data: FSMWorkoutData = cast(FSMWorkoutData, await state.get_data())

    match data.get('training_category', None):
        case TrainingCategory.CLIMBING:
            await message.answer(JOURNAL['fsm_add_content_climb'])
            await message.answer(JOURNAL['fsm_add_content_climb_ex'])
        case TrainingCategory.GYM:
            await message.answer(JOURNAL['fsm_add_content_gym'])
        case _:
            raise exc.JournalError(
                f'Trainig category [state_data] not founded: {data.get('training_category', None)}'
            )

    await state.set_state(FSMFillWorkout.add_train_content)

############################# add training content ########################

@workout_router.message(StateFilter(FSMFillWorkout.add_train_content), F.text)
async def process_add_train_content(
        message: Message, state: FSMContext) -> None:
    '''
    Step 3. Add training sets (content).
    '''
    message = assure_message_from_user_id(message)

    data: FSMWorkoutData = cast(FSMWorkoutData, await state.get_data())
    if not data.get('training_category', None):
        raise exc.JournalError(f"no FSMWorkoutData['training_category']'")

    is_valid = JournalService.training_sets_validation(
        text=message.text or '',
        training_cat=data['training_category']
    )

    logger.info(f'user message: {message.text}')
    logger.info(f'is valid: {is_valid}')
    logger.info(f"training_cat={data['training_category']}")

    if not is_valid:
        await message.answer(JOURNAL['error_invalid_sets'])
        return

    await state.update_data(content=message.text)
    await message.answer(JOURNAL['fsm_add_comment'])
    await state.set_state(FSMFillWorkout.add_comment)

############################# add comment #################################

@workout_router.message(StateFilter(FSMFillWorkout.add_comment), F.text)
async def process_add_train_comment(
        message: Message, state: FSMContext) -> None:
    '''
    Step 4. Add comment to the train.
    '''
    await state.update_data(comments=message.text)
    await state.set_state(FSMFillWorkout.check)
    data: FSMWorkoutData = cast(FSMWorkoutData, await state.get_data())
    await message.answer(
        text=JOURNAL['fsm_to_check'].format(data),
        reply_markup=wrk_write_kboard)
    

############################# add to DB ####################################

@workout_router.callback_query(
        StateFilter(FSMFillWorkout.check),
        F.data.in_(['correct']))
async def process_check_workout(
        cback: CallbackQuery, state: FSMContext,
        journal_service: JournalService) -> None:
    '''
    Step 6. Check & push into DB
    '''
    await cback.answer()
    message = assure_callback_message(cback)

    tg_id = cback.from_user.id
    data: FSMWorkoutDataComplete = cast(FSMWorkoutDataComplete, await state.get_data())

    await journal_service.add_workout(tg_id, data)
    await message.answer(
        text=JOURNAL['fsm_complete'],
        reply_markup=ReplyKeyboardRemove())
    await state.clear()

    logger.info(f'Собранная информация state.get_data(): {data}')
