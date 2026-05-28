import datetime as dt
import logging
import re
from typing import Sequence

from app.domain.enums import TrainingCategory, TrainingType
from app.domain.models import (
    ClimbTrain,
    Exercise,
    GymTrain,
    Route,
    Row,
    Workout,
)

logger = logging.getLogger(__name__)


class JournalParser:
    """Workout parser to get info from user message."""

    @classmethod
    def parse_rows(cls, text: str, training_category: TrainingCategory) -> Sequence[Row]:
        """Extract gym/climbing training rows from user's input."""

        match training_category:
            case TrainingCategory.CLIMBING:
                return cls._parse_rows_climbing(text)
            case TrainingCategory.GYM:
                return cls._parse_rows_gym(text)
            case _:
                raise TypeError(f"Incorrect trainig category: {training_category}")

    @classmethod
    def parse_workout(cls, workout_date: dt.date, training_category: TrainingCategory,
            training_type: TrainingType, content: str, comments: str) -> Workout:
        """Create Workout from FSM data"""
        rows = list(cls.parse_rows(content, training_category=training_category))

        match training_category:
            case TrainingCategory.CLIMBING:
                train = ClimbTrain(
                    type=training_type, rows=rows, comments=comments)
            case TrainingCategory.GYM:
                train = GymTrain(
                    type=training_type, rows=rows, comments=comments)
            case _:
                raise ValueError(f'Incorrect trainig category: {training_category}')

        return Workout(
            date=workout_date, content=[train])

    @classmethod
    def get_route(cls, raw_route: str) -> Route:
        """Use to extract Route from user's message.

        Format:
        6a - просто 6а
        6a+ - просто 6а+
        6a f - 6а флэш
        6a rp - 6а ред поинт
        6a: - 6а со срывом (количество не указано)
        6a:5 - 6а с пятью срывами
        """

        match = re.fullmatch(
            r'(?P<grade>[4-9][abcабс]\+?)(?P<falls>:(?P<falls_no>\d+)?)?(?P<flash>\sf)?(?P<rp>\srp)?',
            raw_route
        )
        if not match or match["grade"] is None:
            raise ValueError(f"Incorrent climbing grade: {raw_route}")

        grade = match["grade"]
        falls = bool(match["falls"])
        if n := match["falls_no"]:
            falls = int(n)
        flash = bool(match["flash"])
        rp = bool(match["rp"])

        return Route(grade=grade, falls=falls, flash=flash, red_point=rp)

    @classmethod
    def _parse_rows_gym(cls, text: str) -> Sequence[Row]:
        """Use to extract Row[Exercise] from user's message.
        
        name 1 - 1/2/3 - Exercise(name="name", repeats=(1, 2, 3,)) in set
        cool exercise 2 - 10 - 10 reps of cool exercise
        """

        rows: list[Row] = []

        for row in text.splitlines():
            comments = ""

            data = row.strip().split("-")
            if not data or len(data) == 1:
                logging.warning(f"Прервана операция парсинга: {text}")
                return []
            
            if len(data) == 3:
                comments = data[2].strip()
            name, reps = map(str.strip, data[:2])
            reps = tuple(map(int, reps.split("/")))

            try:
                exercise = Exercise(name=name, repeats=reps)
            except ValueError:
                return []

            rows.append(Row(content=(exercise, ), comments=comments))

        return rows

    @classmethod
    def _parse_rows_climbing(cls, text: str) -> Sequence[Row]:
        rows: list[Row] = []

        for line in text.splitlines():
            routes, comments = [], ""
            data = line.split("-")
            if len(data) > 1:
                comments = "".join(data[1:]).strip()

            raw_routes = data[0].split(",")

            for r in raw_routes:
                try:
                    routes.append(JournalParser.get_route(r.strip()))
                except ValueError:
                    logging.warning(f"Прервана операция парсинга: {text, r}")
                    return []

            if not len(routes):
                logging.warning(f"Прервана операция парсинга: {text}")
                return []

            rows.append(Row(content=routes, comments=comments))

        return rows
