import datetime as dt
from typing import TypedDict

from aiogram.fsm.state import State, StatesGroup

from app.domain.enums import TrainingCategory, TrainingType


class FSMGetJournal(StatesGroup):
    select_journal = State()

class FSMJournalInfoComplete(TypedDict):
    id: int