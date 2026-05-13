from aiogram.fsm.state import State, StatesGroup


class FSMFillWorkout(StatesGroup):
    select_journal = State()
    add_date = State()
    add_other_date = State()
    add_train_type = State()
    add_train_content = State()
    add_comment = State()