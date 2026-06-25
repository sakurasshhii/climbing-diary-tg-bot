from collections.abc import Sequence

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.domain.enums import TrainingCategory
from app.domain.models import DBJournal
from app.lexic.ru_kboards import (PICK_JOURNAL, TRAIN_CATEGORY,
                                  TRAIN_TYPE_CLIMB, TRAIN_TYPE_GYM,
                                  WORKOUT_DATE, WORKOUT_WRITE)


def build_buttons_from_dict(data: dict[str, str]) -> list[InlineKeyboardButton]:
    return [
        InlineKeyboardButton(text=text, callback_data=cback)
        for cback, text in data.items()
    ]

def get_one_row_kb_from_dict(data: dict[str, str]) -> InlineKeyboardMarkup:
    buttons = build_buttons_from_dict(data)

    return InlineKeyboardMarkup(inline_keyboard=[buttons])

# ———————————————————————————— FSM date ——————————————————————————————————
date_kb = get_one_row_kb_from_dict(WORKOUT_DATE)

# ———————————————————————————— FSM train type ——————————————————————————————————
train_cat_kb = get_one_row_kb_from_dict(TRAIN_CATEGORY)
train_type_kb: dict[TrainingCategory, InlineKeyboardMarkup] = {
    TrainingCategory.CLIMBING: InlineKeyboardMarkup(
        inline_keyboard=[build_buttons_from_dict(TRAIN_TYPE_CLIMB)],
    ),
    TrainingCategory.GYM: InlineKeyboardMarkup(
        inline_keyboard=[build_buttons_from_dict(TRAIN_TYPE_GYM)],
    ),
}

# ———————————————————————————— FSM check ——————————————————————————————————
add_workout_confirm_kb = get_one_row_kb_from_dict(WORKOUT_WRITE)

# ———————————————————————————— select_journal ——————————————————————————————————
def build_journals_kb(journals: Sequence[DBJournal]) -> InlineKeyboardMarkup:
    """Build keyboard with user's journals."""
    journals_kb_builder = InlineKeyboardBuilder()
    journals_kb_builder.row(
        *(
            InlineKeyboardButton(
                text=journal.preview,
                callback_data=str(journal.id),
            )
            for journal in journals
        )
    )
    journals_kb_builder.adjust(1)

    return journals_kb_builder.as_markup()

def get_pick_journal_bttns(has_last: bool, has_choice: bool) -> list[InlineKeyboardButton]:
    buttons = [InlineKeyboardButton(
        text=PICK_JOURNAL["new_journal"],
        callback_data="new_journal")
    ]
    if has_last:
        buttons.append(InlineKeyboardButton(
            text=PICK_JOURNAL["last_journal"],
            callback_data="last_journal")
        )
    if has_choice:
        buttons.append(InlineKeyboardButton(
            text=PICK_JOURNAL["select_journal"],
            callback_data="select_journal")
        )

    return buttons

def build_pick_journal_kb(has_last: bool = True, has_choice: bool = True) -> InlineKeyboardMarkup:
    """Build journal selection keyboard.
    
    Variations: last j / new j / select j.

    has_last — if user have user.last_journal [last_journal bttn].
    has_choice — if user have any created journals [select_journal bttn].
    """
    journ_kb_builder = InlineKeyboardBuilder()
    journ_kb_builder.row(*get_pick_journal_bttns(has_last, has_choice))
    journ_kb_builder.adjust(1)

    return journ_kb_builder.as_markup()
