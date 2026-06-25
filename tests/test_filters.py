import pytest
import datetime as dt

from app.bot.filters.handler_filters import IsCorrectDate


class TestFilterIsCorrectDate:
    filter = IsCorrectDate()

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("text", "expected"),
        (
            ("05.05.2026", dt.date(2026, 5, 5)),
            ("05/05/2026", dt.date(2026, 5, 5)),
            ("05-05-2026", dt.date(2026, 5, 5)),
            ("05.05.9090", dt.date(9090, 5, 5)),
            ("05.05.1001", dt.date(1001, 5, 5)),
            ("05.05.25", dt.date(2025, 5, 5)),
            ("6.8.26", dt.date(2026, 8, 6)),
        ),
    )
    async def test_filter_true(self, text, expected, message_empty):
        message_empty.text = text
        result = await self.filter(message_empty)

        assert result == {"date": expected}

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "text",
        (
            "13.13.2026",
            "01.51.2026",
            "abc",
            "123",
            "1.2",
            "2026",
        ),
    )
    async def test_filter_false(self, text, message_empty):
        message_empty.text = text

        assert await self.filter(message_empty) is False
