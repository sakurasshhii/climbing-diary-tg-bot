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
from aiogram.types import Message, CallbackQuery

from app.bot.states.fsm import FSMFillWorkout
from app.services.services import UserService, JournalService
from app.lexic.ru import JOURNAL

logger = logging.getLogger(__name__)
journal_router = Router()


###################### add workout ######################
###################### functions ########################

async def process_date(
        user_id: int, date: dt.date, state: FSMContext,
        bot_obj: Message | CallbackQuery
):
    # add date
    # await state.update_data(journal_date=?)
    await state.set_state(FSMFillWorkout.add_train_type)

    # ask the train type

###################### handlers #########################
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
        await message.answer(text=JOURNAL['errors_journal_0'])
        await journal_service.add_journal(user_id)
        logger.info(f'Добавлен новый журнал для юзера id={user_id}')

    await state.update_data(journal_no=user.last_journal)
    await message.answer(text=JOURNAL['fsm_add_date'])
    await state.set_state(FSMFillWorkout.add_date)

    # log
    data = await state.get_data()
    logger.info(f'FSM state changed. state.data: {data}')

@journal_router.message(StateFilter(FSMFillWorkout.add_date))
async def process_add_date(
        message: Message, state: FSMContext,
        user_service: UserService) -> None:
    '''
    Step 2. Add a date of workout.
    '''
    # show keyboard
    pass

@journal_router.callback_query(
        StateFilter(FSMFillWorkout.add_date),
        F.data.in_(['today', 'yesterday']))
async def process_add_date_press(
        cback: CallbackQuery, state: FSMContext) -> None:
    if not cback.from_user:
        raise hand_e.NoInfoFromUserError(__name__)
    
    user_id = cback.from_user.id
    if F.data == 'today':
        date = dt.date.today()
    else:
        date = dt.date.today() - dt.timedelta(days=1)

    await process_date(
        user_id=user_id, state=state, date=date, bot_obj=cback)

@journal_router.callback_query(
        StateFilter(FSMFillWorkout.add_date),
        F.data.in_(['other_date']))
async def process_add_date_press_other(
        cback: CallbackQuery, state: FSMContext) -> None:
    # message: write down a date
    pass

@journal_router.message(
        StateFilter(FSMFillWorkout.add_date),
        F.text.regexp(r'\d{4}-\d{2}-\d{2}'))
async def process_add_date_other(
        message: Message, state: FSMContext) -> None:
    if not message.from_user:
        raise hand_e.NoInfoFromUserError(__name__)
    
    user_id = message.from_user.id
    date = dt.date.fromisoformat(message.text)  # type: ignore

    await process_date(
        user_id=user_id, state=state, date=date, bot_obj=message)

@journal_router.message(
        StateFilter(FSMFillWorkout.add_date),
        F.text)
async def process_add_date_other_error(
        message: Message, state: FSMContext) -> None:
    # not valid date
    pass

@journal_router.callback_query(
        StateFilter(FSMFillWorkout.add_train_type),
        F.data.in_(['climb_train', 'gym_train']))
async def process_add_train_type(
        cback: CallbackQuery, state: FSMContext) -> None:
    '''
    Step 3. Add the training type.
    '''
    if not cback.from_user:
        raise hand_e.NoInfoFromUserError(__name__)
    
    user_id = cback.from_user.id
    # add train type
    # ask train content
    await state.set_state(FSMFillWorkout.add_train_content)

@journal_router.message(StateFilter(FSMFillWorkout.add_train_content), F.text)
async def process_add_train_content(
        message: Message, state: FSMContext) -> None:
    '''
    Step 3. Add training sets (content).
    '''
    pass
    # add train content
    await state.set_state(FSMFillWorkout.add_comment)

@journal_router.message(StateFilter(FSMFillWorkout.add_comment), F.text)
async def process_add_train_comment(
        message: Message, state: FSMContext) -> None:
    '''
    Step 4. Add comment to the train.
    '''
    pass
    # add train comment
    await state.set_state(FSMFillWorkout.check)

@journal_router.message(StateFilter(FSMFillWorkout.check))
async def process_check_workout(
        message: Message, state: FSMContext,
        journal_service: JournalService) -> None:
    '''
    Step 6. Check & push
    '''
    if not message.from_user:
        raise hand_e.NoInfoFromUserError(__name__)
    
    user_id = message.from_user.id
    data: dict = await state.get_data()
    await journal_service.add_workout(user_id, **data)