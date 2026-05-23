from aiogram.types import (
    KeyboardButton,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from app.lexic.ru_kboards import (
    WORKOUT_DATE, TRAINING_TYPE, WORKOUT_WRITE,
    TRAIN_TYPE_CLIMB, TRAIN_TYPE_GYM
)
from app.domain.enums import TrainingType, TrainingCategory


builder = ReplyKeyboardBuilder()

################################ date #################################
date_buttons = [
    InlineKeyboardButton(text=text, callback_data=cback)
    for cback, text in WORKOUT_DATE.items()
]
date_kboard = InlineKeyboardMarkup(
    inline_keyboard=[date_buttons[:-1], [date_buttons[-1]]],
    resize_keyboard=True,
    one_time_keyboard=True
)

################################ train type #################################
train_type_buttons = [
    [InlineKeyboardButton(text=text, callback_data=cback)]
    for cback, text in TRAINING_TYPE.items()
]
train_type_kboard = InlineKeyboardMarkup(
    inline_keyboard=train_type_buttons,
    resize_keyboard=True,
    one_time_keyboard=True
)
climb_train_buttons = [
    [InlineKeyboardButton(text=text, callback_data=cback)]
    for cback, text in TRAIN_TYPE_CLIMB.items()
]
climb_train_kboard = InlineKeyboardMarkup(
    inline_keyboard=climb_train_buttons,
    resize_keyboard=True,
    one_time_keyboard=True
)
gym_train_buttons = [
    [InlineKeyboardButton(text=text, callback_data=cback)]
    for cback, text in TRAIN_TYPE_GYM.items()
]
gym_train_kboard = InlineKeyboardMarkup(
    inline_keyboard=gym_train_buttons,
    resize_keyboard=True,
    one_time_keyboard=True
)
train_kboard: dict[TrainingCategory, InlineKeyboardMarkup] = {
    TrainingCategory.CLIMBING: climb_train_kboard,
    TrainingCategory.GYM: gym_train_kboard
}

################################ check workout #################################
wrk_write_buttons = [
    [InlineKeyboardButton(text=text, callback_data=cback)]
    for cback, text in WORKOUT_WRITE.items()
]
wrk_write_kboard = InlineKeyboardMarkup(
    inline_keyboard=wrk_write_buttons,
    resize_keyboard=True,
    one_time_keyboard=True
)