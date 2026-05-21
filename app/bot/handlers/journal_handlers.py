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

import app.bot.handlers.exceptions as hand_e

from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove

from app.bot.states.fsm import FSMFillWorkout
from app.services.services import UserService, JournalService
from app.bot.keyboards.journal_keyboards import (
    date_kboard, train_type_kboard, wrk_write_kboard,
    gym_train_kboard, climb_train_kboard
)
from app.lexic.ru import JOURNAL, MAIN_MENU_MSG

logger = logging.getLogger(__name__)
journal_router = Router()


###################### functions ########################

async def process_date(
        user_id: int, date: dt.date, state: FSMContext,
        message: Message
):
    await state.update_data(workout_date=date)
    await state.set_state(FSMFillWorkout.add_train_type)
    await message.answer(
        text=JOURNAL['fsm_add_train_type'],
        reply_markup=train_type_kboard)

############################ escape ##########################################

@journal_router.message(Command(commands='cancel'), ~StateFilter(default_state))
async def cancel_processing(
        message: Message, state: FSMContext) -> None:
    user_state = await state.get_state()
    logging.info(f'Пользователь прервал операцию на состоянии: {user_state}')
    await state.clear()
    await message.answer(MAIN_MENU_MSG['/cancel'])

############################# fill form ######################################
'''
/add_workout
Start FSM process of colleting workout data & update database.
'''
@journal_router.message(Command(commands='add_workout'), StateFilter(default_state))
async def process_add_workout_command(
        message: Message, state: FSMContext,
        user_service: UserService,
        journal_service: JournalService) -> None:
    '''
    Default way to add workout.
    The last one journal will be selected by default.
    If there are no journal — it creates automatically.
    '''
    if not message.from_user:
        raise hand_e.NoInfoFromUserError(__name__)
    
    user_id = message.from_user.id
    user = await user_service.get_user_assured(user_id)

    if user.last_journal == 0:
        await message.answer(text=JOURNAL['error_journal_0'])
        await journal_service.add_journal(user_id)
        logger.info(f'Добавлен новый журнал для юзера id={user_id}')
        user = await user_service.get_user_assured(user_id)

    await state.update_data(journal_no=user.last_journal)
    await state.set_state(FSMFillWorkout.add_date)
    await message.answer(
        text=JOURNAL['fsm_add_date'],
        reply_markup=date_kboard)

    # log
    data = await state.get_data()
    logger.info(f'FSM state changed. state.data: {data}')

############################# add a date #####################################

@journal_router.callback_query(
        StateFilter(FSMFillWorkout.add_date),
        F.data.in_(['today', 'yesterday']))
async def process_add_date_press(
        cback: CallbackQuery, state: FSMContext) -> None:
    if not cback.from_user:
        raise hand_e.NoInfoFromUserError(__name__)

    user_id = cback.from_user.id
    if cback.data == 'today':
        date = dt.date.today()
    else:
        date = dt.date.today() - dt.timedelta(days=1)

    await process_date(
        user_id=user_id, state=state, date=date, message=cback.message)  # type: ignore

@journal_router.callback_query(
        StateFilter(FSMFillWorkout.add_date),
        F.data.in_(['other_date']))
async def process_add_date_press_other(
        cback: CallbackQuery, state: FSMContext) -> None:
    if not cback.from_user or not cback.message:
        raise hand_e.NoInfoFromUserError(__name__)

    await cback.message.answer(
        JOURNAL['fsm_other_date'],
        reply_markup=ReplyKeyboardRemove())

@journal_router.message(
        StateFilter(FSMFillWorkout.add_date),
        F.text.regexp(r'^\d{4}-\d{2}-\d{2}$'))               # add date filter
async def process_add_date_other(
        message: Message, state: FSMContext) -> None:
    if not message.from_user:
        raise hand_e.NoInfoFromUserError(__name__)
    
    user_id = message.from_user.id
    try:
        date = dt.date.fromisoformat(message.text)             # type: ignore
    except TypeError as e:
        await message.answer(JOURNAL['error_invalid_date'])

    await process_date(
        user_id=user_id, state=state, date=date, message=message)

@journal_router.message(
        StateFilter(FSMFillWorkout.add_date),
        F.text)
async def process_add_date_other_error(
        message: Message) -> None:
    if not message.from_user:
        raise hand_e.NoInfoFromUserError(__name__)
    await message.answer(JOURNAL['error_invalid_date'])

############################# add training type ########################

@journal_router.callback_query(
        StateFilter(FSMFillWorkout.add_train_type),
        F.data.in_(['climbing', 'gym']))
async def process_add_train_type(
        cback: CallbackQuery, state: FSMContext) -> None:
    '''
    Step 3. Add the training type.
    '''
    if not cback.from_user or not cback.message:
        raise hand_e.NoInfoFromUserError(__name__)

    await state.update_data(training_category=cback.data)
    match cback.data:
        case 'climbing':
            await cback.message.edit_reply_markup(       # type: ignore
                reply_markup=climb_train_kboard
            )
        case _:
            await cback.message.edit_reply_markup(       # type: ignore
                reply_markup=gym_train_kboard
            )

@journal_router.callback_query(
    StateFilter(FSMFillWorkout.add_train_type),
    F.data.in_(['boulder', 'lead', 'SFP', 'GPP']))
async def process_add_train_subtype(
    cback: CallbackQuery, state: FSMContext) -> None:

    if not cback.from_user or not cback.message:
        raise hand_e.NoInfoFromUserError(__name__)
    await state.update_data(training_type=cback.data)
    await state.set_state(FSMFillWorkout.add_train_content)

    state_data = await state.get_data()
    match state_data['training_category']:
        case 'climbing':
            await cback.message.answer(JOURNAL['fsm_add_content_climb'])
            await cback.message.answer(JOURNAL['fsm_add_content_climb_ex'])
        case _:
            await cback.message.answer(JOURNAL['fsm_add_content_gym'])

############################# add training content ########################

@journal_router.message(StateFilter(FSMFillWorkout.add_train_content), F.text)
async def process_add_train_content(
        message: Message, state: FSMContext) -> None:
    '''
    Step 3. Add training sets (content).
    '''
    if message.text:
        workout_data = await state.get_data()
        is_valid = JournalService.training_sets_validation(
            text=message.text,
            training_cat=workout_data['training_category']
        )
        
        logger.info(f'user message: {message.text}')
        logger.info(f'is valid: {is_valid}')
        logger.info(f'args [training_cat=workout_data["training_category"]]:{workout_data['training_category']}')

        if not is_valid:
            await message.answer(JOURNAL['error_invalid_sets'])
            return

        await state.update_data(content=message.text)
        await state.set_state(FSMFillWorkout.add_comment)
        await message.answer(JOURNAL['fsm_add_comment'])

############################# add comment #################################

@journal_router.message(StateFilter(FSMFillWorkout.add_comment), F.text)
async def process_add_train_comment(
        message: Message, state: FSMContext) -> None:
    '''
    Step 4. Add comment to the train.
    '''
    await state.update_data(comments=message.text)
    await state.set_state(FSMFillWorkout.check)
    data = await state.get_data()
    await message.answer(
        text=JOURNAL['fsm_to_check'].format(data),
        reply_markup=wrk_write_kboard)
    

############################# add to DB ####################################

@journal_router.callback_query(
        StateFilter(FSMFillWorkout.check),
        F.data.in_(['correct']))
async def process_check_workout(
        cback: CallbackQuery, state: FSMContext,
        journal_service: JournalService) -> None:
    '''
    Step 6. Check & push into DB
    '''
    if not cback.from_user or not cback.message:
        raise hand_e.NoInfoFromUserError(__name__)

    user_id = cback.from_user.id
    data: dict = await state.get_data()
    await journal_service.add_workout(user_id, **data)
    await cback.message.answer(
        text=JOURNAL['fsm_complete'],
        reply_markup=ReplyKeyboardRemove())
    await state.clear()

    logger.info(f'Собранная информация state.get_data(): {data}')