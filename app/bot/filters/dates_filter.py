import datetime as dt
import re

from aiogram.filters import BaseFilter
from aiogram.types import Message


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


if __name__ == "__tests__":
    filter = IsCorrectDate()
    for date in (
        "05.05.2026",
        "05/05/2026",
        "05-05-2026",
        "05.05.9090",
        "05.05.1001",
        "05.05.25",
        "6.8.26"
    ):
        print(filter(date), date)  # correct
    for date in (
        "13.13.2026",
        "01.51.2026",
    ):
        print(filter(date), date)  # incorrect
