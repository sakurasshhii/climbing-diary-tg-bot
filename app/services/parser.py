import datetime as dt
import json
import logging
import re
from dataclasses import asdict
from typing import Sequence

from app.domain.enums import TrainingCategory, TrainingType
from app.domain.models import (ClimbTrain, Exercise, GymTrain, Route, Row,
                               Workout)

logger = logging.getLogger(__name__)


class JournalParser:
    """Workout parser to get info from user message."""

    PATTERN_ROUTE = re.compile(r"(?P<grade>[4-9][abc]\+?)(?P<falls>:(?P<falls_no>\d+)?)?(?P<flash>\sf)?(?P<rp>\srp)?")
    CHAR_CORRESPONDENCE = {"а": "a", "б": "b", "с": "c",}

    @classmethod
    def parse_rows(cls, text: str, training_category: TrainingCategory) -> Sequence[Row]:
        """Extract gym/climbing training rows from user's input."""

        match training_category:
            case TrainingCategory.CLIMBING:
                return cls._parse_rows_climbing(text)
            case TrainingCategory.GYM:
                return cls._parse_rows_gym(text)

    @classmethod
    def parse_workout(cls, workout_date: dt.date, training_category: TrainingCategory,
            training_type: TrainingType, content: list[Row], comments: str) -> Workout:
        """Create Workout from FSM data"""

        match training_category:
            case TrainingCategory.CLIMBING:
                train = ClimbTrain(
                    type=training_type, rows=content, comments=comments)
            case TrainingCategory.GYM:
                train = GymTrain(
                    type=training_type, rows=content, comments=comments)

        return Workout(
            date=workout_date, content=[train])

    @classmethod
    def dumps_rows(cls, rows: Sequence[Row]) -> str:
        data = []
        if not rows:
            return ""

        for r in rows:
            d = asdict(r)
            del d["training_category"]
            data.append(d)

        return json.dumps(data, ensure_ascii=True)

    @classmethod
    def loads_sets(cls, raw: str, training_category: TrainingCategory) -> list[Row]:
        data = json.loads(raw)
        return list(cls._loads_row(x, training_category) for x in data)

    @classmethod
    def _loads_row(cls, row: dict, training_category: TrainingCategory) -> Row:
        content = row.get("content", [])
        if training_category == TrainingCategory.CLIMBING:
            row["content"] = tuple(Route(**r) for r in content)
        elif training_category == TrainingCategory.GYM:
            row["content"] = tuple(Exercise(**e) for e in content)

        return Row(**row)

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

        for old, new in cls.CHAR_CORRESPONDENCE.items():
            raw_route = raw_route.replace(old, new)

        match = cls.PATTERN_ROUTE.fullmatch(raw_route)
        if not match or match["grade"] is None:
            raise ValueError(f"Incorrent climbing grade: {raw_route}")

        grade = match["grade"]
        falls_no = 0
        if bool(match["falls"]):
            falls_no = int(match["falls_no"]) if match["falls_no"] else 1
        flash = bool(match["flash"])
        rp = bool(match["rp"])

        return Route(grade=grade, falls_no=falls_no, flash=flash, red_point=rp)

    @classmethod
    def _parse_rows_gym(cls, text: str) -> Sequence[Row]:
        """Use to extract Row[Exercise] from user's message.
        
        name 1 - 1/2/3 - Exercise(name="name", repeats=(1, 2, 3,)) in set
        cool exercise 2 - 10 - 10 reps of cool exercise
        """

        rows: list[Row] = []

        for row in text.splitlines():
            comments = ""

            data = tuple(map(str.strip, row.strip().split("-")))
            if not data or len(data) <= 1:
                logging.warning(f"Прервана операция парсинга: {text}")
                return []

            if len(data) == 3:
                comments = data[2].strip()
            name, reps = map(str.strip, data[:2])

            try:
                reps = tuple(map(int, reps.split("/")))
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
            data = tuple(map(str.strip, line.split("-")))

            if len(data) > 1:
                comments = "-".join(data[1:])

            if data and data[0]:
                raw_routes = data[0]

                for old, new in cls.CHAR_CORRESPONDENCE.items():
                    raw_routes = raw_routes.replace(old, new)

                for r in map(str.strip, raw_routes.split(",")):
                    try:
                        routes.append(cls.get_route(r))
                    except ValueError:
                        logging.warning(f"Прервана операция парсинга: {text, r}")
                        return []
            else:
                continue

            rows.append(Row(content=routes, comments=comments))

        return rows
