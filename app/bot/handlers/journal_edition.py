'''
Module contains handlers to manage journal.

-- UI & FSM schema --
(journal / Workout creation)

1. select a journal
    (button: create new / last one / pick from the list)
2.1 add a date
    (button: today / yesterday / other date — write down)
2.2* write a date if other date selected
3. add training type
    (button: ClimbTrain / GymTrain <class Train>)
4. add training content
    (write text: routes / workouts as in the example)
5. add comment
    (write any text)
'''
import logging

from aiogram import Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import Message

from app.bot.states.fsm import FSMFillWorkout
from app.infrastructure.database import UserRepository
from app.lexic.ru import JOURNAL

logger = logging.getLogger(__name__)
journal_router = Router()


'''
/add_workout

Start FSM process of colleting workout. Output data intend to database.
'''
@journal_router.message(Command(commands='add_workout'), StateFilter(default_state))
async def process_add_workout_command(
    message: Message,
    state: FSMContext,
    user_repo: UserRepository
) -> None:
    '''
    Default way to add workout. Last one journal will be selected by default.
    '''
    if message.from_user:
        user_id = message.from_user.id
        user = await user_repo.get_user_assured(user_id)
        journal_no = user['last_journal']

        if journal_no == 0:
            await message.answer(text=JOURNAL['errors_journal_0'])
            await user_repo.add_journal(user_id)
            journal_no = user['last_journal']
            logger.info(f'Добавлен новый журнал для юзера id={user_id}')
        
        await state.update_data(journal_no=journal_no)
        await message.answer(text=JOURNAL['fsm_add_date'])
        await state.set_state(FSMFillWorkout.add_date)

        data = await state.get_data()
        logger.info(f'FSM state changed. state.data: {data}')

@journal_router.message(StateFilter(FSMFillWorkout.add_date))
async def process_add_date(
    message: Message,
    state: FSMContext,
    user_repo: UserRepository
) -> None:
    pass