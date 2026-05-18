from aiogram.types import (
    KeyboardButton,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from app.lexic.ru_kboards import WORKOUT_DATE, TRAIN_TYPE, WORKOUT_WRITE


builder = ReplyKeyboardBuilder()

##################### date ####################
date_buttons = [
    InlineKeyboardButton(text=text, callback_data=cback)
    for cback, text in WORKOUT_DATE.items()
]
date_kboard = InlineKeyboardMarkup(
    inline_keyboard=[date_buttons[:-1], [date_buttons[-1]]],
    resize_keyboard=True,
    one_time_keyboard=True
)

train_type_buttons = [
    [InlineKeyboardButton(text=text, callback_data=cback)]
    for cback, text in TRAIN_TYPE.items()
]
train_type_kboard = InlineKeyboardMarkup(
    inline_keyboard=train_type_buttons,
    resize_keyboard=True,
    one_time_keyboard=True
)

wrk_write_buttons = [
    [InlineKeyboardButton(text=text, callback_data=cback)]
    for cback, text in WORKOUT_WRITE.items()
]
wrk_write_kboard = InlineKeyboardMarkup(
    inline_keyboard=wrk_write_buttons,
    resize_keyboard=True,
    one_time_keyboard=True
)