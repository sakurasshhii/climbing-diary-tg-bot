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
    def is_valid_rows(cls, text: str, training_category: TrainingCategory) -> Sequence[Row] | None:
        try:
            return cls.parse_rows(text, training_category)
        except ValueError as e:
            return None

    @classmethod
    def parse_rows(cls, text: str, training_category: TrainingCategory) -> Sequence[Row]:
        """Extract gym/climbing training rows from user's input."""

        if training_category == TrainingCategory.CLIMBING:
            return cls.parse_rows_climbing(text)
        elif training_category == TrainingCategory.GYM:
            return cls.parse_rows_gym(text)
        else:
            raise TypeError(f"Incorrect trainig category: {training_category}")

    @classmethod
    def parse_rows_gym(cls, text: str) -> Sequence[Row]:
        rows: list[Row] = []

        for row in text.splitlines():
            match = re.fullmatch(r"(?P<name>[\w\s]+)\s(?P<repeats>[\d/]+)/?\s?(?P<comments>.+)?", row)
            if not match:
                logging.warning(f"Прервана операция парсинга: {text}")
                return []

            repeats = tuple(map(int, match["repeats"].strip("/").split("/")))
            exercise = Exercise(name=match["name"], repeats=repeats)
            rows.append(
                Row(content=(exercise, ), comments=match["comments"] or "")
            )

        return rows

    @classmethod
    def parse_rows_climbing(cls, text: str) -> Sequence[Row]:
        rows: list[Row] = []

        for line in text.splitlines():
            routes, comments = [], ""

            for elm in line.split("/"):
                try:
                    routes.append(JournalParser.get_route(elm))
                except ValueError:
                    comments = elm
            if not routes:
                logging.warning(f"Прервана операция парсинга: {text}")
                return []

            rows.append(
                Row(content=tuple(routes), comments=comments)
            )

        return rows

    @classmethod
    def get_route(cls, text: str) -> Route:
        """Use to extract Route from user's message."""

        match = re.fullmatch(r'(?P<grade>\d[abcабс]\+?)(?P<falls>\s\d)?', text)
        if not match or match["grade"] is None:
            raise ValueError(f"Incorrent climbing grade: {text}")

        flash = False
        grade, falls = [m.strip() if m else False for m in match.groups()]
        grade = str(grade)
        for old, new in zip("абс", "abc"):
            grade = grade.replace(old, new)
        if falls == "0":
            flash = True
        elif not falls:
            falls = 0

        return Route(grade=grade, falls=int(falls), flash=flash)
