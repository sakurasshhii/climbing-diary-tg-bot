import datetime as dt

from typing import TypedDict
from aiogram.fsm.state import State, StatesGroup
from app.domain.enums import TrainingCategory, TrainingType


class FSMFillWorkout(StatesGroup):
    select_journal = State()
    add_date = State()
    add_other_date = State()
    add_train_type = State()
    add_train_content = State()
    add_comment = State()
    check = State()

class FSMWorkoutDataComplete(TypedDict):
    journal_no: int
    workout_date: dt.date
    training_category: TrainingCategory
    training_type: TrainingType
    content: str
    comments: str

class FSMWorkoutData(FSMWorkoutDataComplete, total=False):
    pass