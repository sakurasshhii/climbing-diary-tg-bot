import pytest
from app.services.parser import JournalParser
from app.domain.enums import TrainingCategory
from app.domain.models import Row, Route, Exercise
from app.domain.enums import TrainingCategory
from app.domain.models import Row, Route, Exercise


class TestParser:
    @pytest.mark.parametrize(
        "route",
        "6a, 6a+, 6a:1, 6a:5, 6a:, 6a f, 6a rp, 6a+ f, 6a+ rp, 6a:10".split(", ")
    )
    def test_get_route_ok(self, route):
        assert JournalParser.get_route(route)

    @pytest.mark.parametrize(
        "route",
        "6d, 3a, 10b, 6a+: f, 6a f rp, 6a: rp, 6a: f rp, 6a d, 6a:100".split(", ")
    )
    def test_get_route_invalid(self, route):
        with pytest.raises(ValueError):
            JournalParser.get_route(route)
    
    @pytest.mark.parametrize(
    "text,training_category,expected",
    [(
        """6a, 6a+ - first
        6b:, 6b f - second
        6c rp""",
        TrainingCategory.CLIMBING,
        [
            Row([Route("6a"), Route("6a+")], "first"),
            Row([Route("6b", falls=True), Route("6b", flash=True)], "second"),
            Row([Route("6c", red_point=True)])
        ],
    ), (
        "6a",
        TrainingCategory.CLIMBING,
        [Row([Route("6a")])],
    ), (
        """exercise 1 - 1/2/3
        cool exercise - 1
        strange exercise - 100 - strange""",
        TrainingCategory.GYM,
        [
            Row([Exercise(name="exercise 1", repeats=(1, 2, 3))]),
            Row([Exercise(name="cool exercise", repeats=(1,))]),
            Row([Exercise(name="strange exercise", repeats=(100,))], comments="strange"),
        ],
    ),  (
        "exercise 1 - 1",
        TrainingCategory.GYM,
        [Row([Exercise(name="exercise 1", repeats=(1,))])],
    ),
    ])
    def test_parse_rows_ok(self, text, training_category, expected):
        rows = JournalParser.parse_rows(text=text, training_category=training_category)
        assert rows == expected

    @pytest.mark.parametrize(
        "text,training_category",
        [(
                "6a, 6a+ rp f - first",
                TrainingCategory.CLIMBING,
            ), (
                "exercise 1 - 0/0",
                TrainingCategory.GYM,
            ),
        ]
    )
    def test_parse_rows_invalid(self, text, training_category):
        rows = JournalParser.parse_rows(text=text, training_category=training_category)
        assert rows == []
