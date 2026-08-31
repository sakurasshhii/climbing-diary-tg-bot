import datetime as dt
from typing import TypedDict

from aiogram.fsm.state import State, StatesGroup

from app.domain.enums import TrainingCategory, TrainingType


class FSMUserMenu(StatesGroup):
    """Operations with /edit_journals menu."""

    journal_menu = State()


class FSMGetJournal(StatesGroup):
    select_journal = State()


class FSMJournalInfoComplete(TypedDict):
    """State info to get journal."""

    id: int


class FSMAddJournal(StatesGroup):
    input_name = State()
    input_comments = State()


class FSMJournalComplete(TypedDict):
    journal_name: str
    journal_comments: str


class FSMDeleteJournal(StatesGroup):
    select_journal = State()
    confirm_del = State()


class FSMEditJournal(StatesGroup):
    select_journal = State()
    edit_name = State()
    edit_comments = State()
