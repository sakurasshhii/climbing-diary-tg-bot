import datetime as dt
import re
from typing import Any

from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery


class IsCorrectDate(BaseFilter):
    async def __call__(self, message: Message) -> bool | dict[str, dt.date]:
        date: str = message.text or ""
        match = re.fullmatch(r"(\d{1,2}).(\d{1,2}).(\d{2,4})", date)
        if match and len(match.groups()) == 3:
            try:
                d, m, y = map(int, match.groups())
                if y < 1000:
                    y += 2000

                return {"date": dt.date(year=y, month=m, day=d)}
            except (TypeError, ValueError):
                return False

        return False


class Isalnum(BaseFilter):
    async def __call__(self, cback: CallbackQuery) -> bool:
        no: str = cback.data or ""
        return no.isalnum()
