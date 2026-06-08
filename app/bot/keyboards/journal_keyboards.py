from collections.abc import Iterable

from aiogram.types import (InlineKeyboardButton, InlineKeyboardMarkup,
                           KeyboardButton, ReplyKeyboardMarkup)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from app.domain.enums import TrainingCategory, TrainingType
from app.domain.models import DBJournal
from app.lexic.ru_kboards import (TRAIN_CATEGORY, TRAIN_TYPE_CLIMB,
                                  TRAIN_TYPE_GYM, WORKOUT_DATE, WORKOUT_WRITE,
                                  PICK_JOURNAL)

# ———————————————————————————— FSM date ——————————————————————————————————
date_buttons = [
    InlineKeyboardButton(text=text, callback_data=cback)
    for cback, text in WORKOUT_DATE.items()
]
date_kboard = InlineKeyboardMarkup(
    inline_keyboard=[date_buttons[:-1], [date_buttons[-1]]],
    resize_keyboard=True,
    one_time_keyboard=True
)

# ———————————————————————————— FSM train type ——————————————————————————————————
train_cat_buttons = [
    [InlineKeyboardButton(text=text, callback_data=cback)]
    for cback, text in TRAIN_CATEGORY.items()
]
train_cat_kboard = InlineKeyboardMarkup(
    inline_keyboard=train_cat_buttons,
    resize_keyboard=True,
    one_time_keyboard=True
)
climb_train_buttons = [
    [InlineKeyboardButton(text=text, callback_data=cback)]
    for cback, text in TRAIN_TYPE_CLIMB.items()
]
gym_train_buttons = [
    [InlineKeyboardButton(text=text, callback_data=cback)]
    for cback, text in TRAIN_TYPE_GYM.items()
]

train_type_kboard: dict[TrainingCategory, InlineKeyboardMarkup] = {
    TrainingCategory.CLIMBING: InlineKeyboardMarkup(
        inline_keyboard=climb_train_buttons,
        resize_keyboard=True,
        one_time_keyboard=True
    ),
    TrainingCategory.GYM: InlineKeyboardMarkup(
        inline_keyboard=gym_train_buttons,
        resize_keyboard=True,
        one_time_keyboard=True
    ),
}

# ———————————————————————————— FSM check ——————————————————————————————————
check_buttons = [
    [InlineKeyboardButton(text=text, callback_data=cback)]
    for cback, text in WORKOUT_WRITE.items()
]
check_kboard = InlineKeyboardMarkup(
    inline_keyboard=check_buttons,
    resize_keyboard=True,
    one_time_keyboard=True
)

# ———————————————————————————— select_journal ——————————————————————————————————
def journals_as_buttons(journals: Iterable[DBJournal]) -> Iterable[InlineKeyboardButton]:
    return [
        InlineKeyboardButton(
            text=journal.preview,
            callback_data=str(journal.id),
        )
        for journal in journals
    ]

def get_journals_kb(journals: Iterable[DBJournal]) -> InlineKeyboardMarkup:
    "Get keyboard from journals list."
    buttons = journals_as_buttons(journals)
    journals_kb_builder = InlineKeyboardBuilder()
    journals_kb_builder.row(*buttons)
    journals_kb_builder.adjust(1)

    return journals_kb_builder.as_markup()

pick_journal_bttns: Iterable[InlineKeyboardButton] = [
    InlineKeyboardButton(
        text = t,
        callback_data=key
    ) for key, t in PICK_JOURNAL.items()
]

def get_pick_j_kb() -> InlineKeyboardMarkup:
    "Get kb for chose: last j / new j / select j."
    journ_kb_builder = InlineKeyboardBuilder()
    journ_kb_builder.row(*pick_journal_bttns)
    journ_kb_builder.adjust(1)

    return journ_kb_builder.as_markup()
