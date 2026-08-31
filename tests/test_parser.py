import pytest

from app.domain.enums import TrainingCategory, TrainingType
from app.domain.models import (ClimbTrain, Exercise, GymTrain, Route, Row,
                               Workout)
from app.services.parser import JournalParser


class TestParser:
    @pytest.mark.parametrize(
        "route",
        "6a, 6a+, 6a:1, 6a:5, 6a:, 6a f, 6a rp, 6a+ f, 6a+ rp, 6a:10, 6а, 6б, 6с".split(", ")
    )
    def test_get_route_ok(self, route):
        assert JournalParser.get_route(route)

    @pytest.mark.parametrize(
        "route",
        "6d, 3a, 10b, 6a+: f, 6a f rp, 6a: rp, 6a: f rp, 6a d, 6a:-5".split(", ")
    )
    def test_get_route_invalid(self, route):
        with pytest.raises(ValueError):
            JournalParser.get_route(route)

    @pytest.mark.parametrize(
    "text,training_cat,expected",
    [(
        """6a, 6a+ - first
        6b:, 6b f - second
        6c rp""",
        TrainingCategory.CLIMBING,
        [
            Row([Route("6a"), Route("6a+")], "first"),
            Row([Route("6b", falls_no=True), Route("6b", flash=True)], "second"),
            Row([Route("6c", red_point=True)])
        ],
    ), (
        "6a",
        TrainingCategory.CLIMBING,
        [Row([Route("6a")])],
    ),  (
        """6a, 6a+ - first
        """,
        TrainingCategory.CLIMBING,
        [Row([Route("6a"), Route("6a+")], "first")]
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
    def test_parse_rows_ok(self, text, training_cat, expected):
        rows = JournalParser.parse_rows(text=text, training_category=training_cat)
        assert rows == expected

    @pytest.mark.parametrize(
        "text,training_category",
        [(
                "6a, 6a+ rp f - first",
                TrainingCategory.CLIMBING,
            ), (
                " - first",
                TrainingCategory.CLIMBING,
            ), (
                "exercise 1 - 0/0",
                TrainingCategory.GYM,
            ), (
                "exercise 1 - ",
                TrainingCategory.GYM,
            ), (
                " - 1/1/1",
                TrainingCategory.GYM,
            ), (
                "exercise 1 1/1",
                TrainingCategory.GYM,
            ),
        ]
    )
    def test_parse_rows_invalid(self, text, training_category):
        rows = JournalParser.parse_rows(text=text, training_category=training_category)
        assert rows == []

    def test_parse_workout_ok(self, new_date, row_routes, row_exercises):
        w = JournalParser.parse_workout(
            workout_date=new_date,
            training_category=TrainingCategory.CLIMBING,
            training_type=TrainingType.LEAD,
            content=[row_routes],
            comments="-",
        )
        assert w == Workout(
            date=new_date,
            content=[
                ClimbTrain(
                    type=TrainingType.LEAD,
                    rows=[row_routes],
                    comments="",
                )
            ],
            comments=""
        )
        w = JournalParser.parse_workout(
            workout_date=new_date,
            training_category=TrainingCategory.GYM,
            training_type=TrainingType.GPP,
            content=[row_exercises],
            comments="-",
        )
        assert w == Workout(
            date=new_date,
            content=[
                GymTrain(
                    type=TrainingType.GPP,
                    rows=[row_exercises],
                    comments="",
                )
            ],
            comments=""
        )
