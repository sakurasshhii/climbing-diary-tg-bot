import datetime as dt
from typing import TypedDict

from aiogram.fsm.state import State, StatesGroup

from app.domain.enums import TrainingCategory, TrainingType


class FSMGetJournal(StatesGroup):
    select_journal = State()

class FSMJournalInfoComplete(TypedDict):
    """State info to get journal."""

    id: int

class FSMNewJournal(StatesGroup):
    input_name = State()
    input_comment = State()

class FSMNewJournalComplete(TypedDict):
    journal_name: str
    journal_comments: str
