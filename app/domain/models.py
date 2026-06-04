"""models:

1. Классы, существующие для представления информации из БД.
2. Классы, формирующие тренировочный журнал длительностью (описывают тр. цикл).

———————————————————————————— Structure ———————————————————————————

Journal(
    content: list = [Workout(), ...],        # all trainings in training cycle
    period: tuple[dt.date, dt.date],         # start & end date — property
    comments: str | None = None,             # comments to the whole journal
)
Workout(
    date: dt.date,
    content: list[Train] = [
        ClimbTrain(
            type: lead | boulder,
            sets: [Row([Route(rate[str], falls[int], flash[int]), ...], *comments), ...],
        ),
        GymTrain(
            type: GPP | SFP,
            sets: [Row([Exercise(name[str], repeats), ...], *comments), ...],
        )
    ],
    *comments: str | None = None
)

* - not necessarily arguments

———————————————————————————— To do ———————————————————————————————
1. exercise_sets — вместо хранения повторений в json-сериализации / списке
Exercise_sets (exercise_id, weight, reps, order)

2. Добавить возможность круговой тренировки.
На данный момент Exercise всегда существует в Set в одном экземпляре,
    т.е. в одном подходе могут быть повторы только одного упражнения.

3. Добавить журналам название (name) — для более удобного поиска.
На данный момент поиск организован по датам, что особенно неудобно для давних журналов.
"""

from __future__ import annotations

import datetime as dt
import logging
import re
from collections.abc import Sequence
from dataclasses import dataclass, field

import app.domain.exceptions as exc

from .enums import TrainingCategory, TrainingType

logger = logging.getLogger(__name__)


# ———————————————————————————— contstant —————————————————————————————————————————————

DATE_FORMAT = r"%d.%m.%Y"
REP_DELIMITER = "/"

# ———————————————————————————— 1. dataclasses as DB tables ———————————————————————————

@dataclass
class User:
    """User representation from DB table «users»."""

    id: int
    tg_id: int
    username: str
    last_journal: int


@dataclass
class DBJournal:
    """Journal representation from DB table «journals»."""

    id: int
    user_id: int
    comments: str
    period_start: dt.date | None
    period_end: dt.date | None

    def __post_init__(self):
        def convert_date(date) -> dt.date | None:
            return dt.date.fromisoformat(date) if date else None

        if isinstance(self.period_end, str) or isinstance(self.period_start, str):
            self.period_start = convert_date(self.period_start)
            self.period_end = convert_date(self.period_end)

    @property
    def dates(self):
        dates = tuple([
            d.strftime(DATE_FORMAT) if d else "..."
            for d in [self.period_start, self.period_end]
        ])
        return "{} - {}".format(*dates)


@dataclass
class DBWorkout:
    """Workout representation from DB table «workouts»."""

    id: int
    journal_id: int
    workout_date: dt.date
    comments: str

    def __post_init__(self):
        if isinstance(self.workout_date, str):
           self.workout_date = dt.date.fromisoformat(self.workout_date)


@dataclass
class DBTrain:
    """Train representation from DB table «trains»."""

    id: int
    workout_id: int
    category: TrainingCategory
    type: TrainingType
    comments: str

    def __post_init__(self):
        try:
            if isinstance(self.id, str):
                self.id = int(self.id)
            if isinstance(self.workout_id, str):
                self.workout_id = int(self.workout_id)
            if isinstance(self.category, str):
                self.category = TrainingCategory[self.category.upper()]
            if isinstance(self.type, str):
                self.type = TrainingType[self.type.upper()]
        except (ValueError, KeyError):
            logger.exception("Invalid data for DBTrain object.")


@dataclass
class DBRow:
    """Row representation from DB table «rows»."""

    id: int
    train_id: int
    row_order: int
    comments: str

# ———————————————————————————— 2. journal structure ——————————————————————————————————

@dataclass
class Journal:
    """Container of multiple workout sessions."""

    content: list[Workout] = field(default_factory=list)
    comments: str = ""

    def __post_init__(self):
        if self.content:
            if not all(isinstance(x, Workout) for x in self.content):
                raise TypeError("Journal must contain Workout objects only.")
            self.content.sort(key=lambda x: x.date)

        if self.comments == "-":
            self.comments = ""

    @property
    def period(self) -> tuple[dt.date | None, dt.date | None]:
        if self.content:
            return (self.content[0].date, self.content[-1].date)
        return (None, None)

    def add_workout(self, workout: Workout) -> None:
        if not isinstance (workout, Workout):
            raise TypeError("Journal could contain Workout objects only.")

        self.content.append(workout)
        if len(self) >=2 and self.content[-2].date > workout.date:
            self.content.sort(key=lambda x: x.date)

    def __str__(self) -> str:
        date_st, date_en = (
            date.strftime(DATE_FORMAT) if date else "..."
            for date in self.period
        )
        date: str = "Дневник {}-{}".format(date_st, date_en)
        comments: str = f"Комментарии: {self.comments}" if self.comments else ""
        if self.content:
            content: str = "\n——————————\n".join(str(x) for x in self.content)
        else:
            content: str = "Нет тренировок."

        return "\n".join(x for x in (date, comments, " ", content) if x)

    def __len__(self) -> int:
        return len(self.content)


@dataclass
class Workout:
    """One workout session.

    Could contain several training types.
    """

    date: dt.date
    content: list[Train] = field(default_factory=list)
    comments: str = ""

    def __post_init__(self):
        if not isinstance(self.date, dt.date):
            raise exc.MissedDateError(self.date)

        if self.comments == "-":
            self.comments = ""

    def add_train(self, train: Train):
        if not isinstance(train, Train):
            raise TypeError("Workout could contain Train objects only.")
        self.content.append(train)

    @property
    def get_content(self) -> tuple[Train, ...]:
        return tuple(self.content)

    def __str__(self) -> str:
        date = self.date.strftime(DATE_FORMAT)
        content = "\n".join(str(x) for x in self.content)
        comments = f"Комментарии: {self.comments}" if self.comments else ""
        data = [x for x in (date, content, comments) if x]

        return "\n".join(data)


@dataclass(frozen=True)
class Train:
    """Group of the same physical activity.

    Parent class for climbing / gym training.
    """

    training_category: TrainingCategory = field(init=False)
    type: TrainingType
    rows: list[Row] = field(default_factory=list)
    comments: str = ""

    def __post_init__(self) -> None:
        if self.comments == "-":
            object.__setattr__(self, "comments", "")

    @property
    def get_rows(self) -> tuple[Row, ...]:
        return tuple(self.rows)

    def add_row(self, row: Row) -> None:
        if not isinstance(row, Row):
            raise TypeError("Train must contain Row objects only.")
        if not self.training_category == row.training_category:
            raise TypeError("Train must contain one trainig type.")

        self.rows.append(row)

    def set_comment(self, val: str) -> None:
        if len(val) and isinstance(val, str):
            object.__setattr__(self, "comments", val)

    @classmethod
    def from_training_category(
        cls,
        training_category: TrainingCategory,
        type: TrainingType,
        rows: list[Row] = field(default_factory=list),
        comments: str = "",
    ) -> ClimbTrain | GymTrain:
        match training_category:
            case TrainingCategory.CLIMBING:
                return ClimbTrain(type, rows, comments)
            case TrainingCategory.GYM:
                return GymTrain(type, rows, comments)

    def __str__(self) -> str:
        tr_type = {
            TrainingType.LEAD: "Трудность",
            TrainingType.BOULDER: "Боулдер",
            TrainingType.GPP: "ОФП",
            TrainingType.SFP: "СФП",
        }
        content: str = "\n".join(str(r) for r in self.rows)
        comments = f"Комментарии: {self.comments}" if self.comments else ""
        data = [x for x in (tr_type[self.type], content, comments) if x]

        return "\n".join(data)


@dataclass(frozen=True)
class ClimbTrain(Train):
    training_category = TrainingCategory.CLIMBING


@dataclass(frozen=True)
class GymTrain(Train):
    training_category = TrainingCategory.GYM


@dataclass(frozen=True)
class Row:
    """Container grouping one training set."""

    content: Sequence[Route | Exercise]
    comments: str = ""
    training_category: TrainingCategory = field(init=False)

    def __post_init__(self) -> None:
        if not self.content:
            raise ValueError("Empty set is not avaiable.")
        if isinstance(self.content[0], Route):
            object.__setattr__(self, "training_category", TrainingCategory.CLIMBING)
        if isinstance(self.content[0], Exercise):
            object.__setattr__(self, "training_category", TrainingCategory.GYM)
        if self.comments == "-":
            object.__setattr__(self, "comments", "")

        object.__setattr__(self, "content", tuple(self.content))

    def __str__(self) -> str:
        content: str = ", ".join(str(r) for r in self.content)
        comments = f" — {self.comments}" if self.comments else ""

        return content + comments


@dataclass(frozen=True)
class Route:
    """Route rate via French/Fontainebleau system."""

    grade: str                      # French grade from 5a to 9b+
    falls: int | bool = False       # Count of falls in route before top
    flash: bool = False             # Flash flag
    red_point: bool = False         # Red point flag

    def __post_init__(self) -> None:
        if not re.fullmatch(r"\d[abcABC]\+?", self.grade):
            raise ValueError(f"Invalid grade: {self.grade}")
        if not isinstance(self.falls, (int, bool)) or self.falls < 0 or self.falls > 50:
            raise ValueError(f"Invalid falls count: {self.falls}")
        if not isinstance(self.flash, bool) or self.flash and self.falls:
            raise ValueError(f"Invalid flash flag: {self.flash}")
        if not isinstance(self.red_point, bool) or \
            self.red_point and self.falls or \
            self.red_point and self.flash:
            raise ValueError("Red point flag failed")

    def __str__(self) -> str:
        info = []
        if self.falls:
            info.append(":")
            if not isinstance(self.falls, bool):
                info.append(str(self.falls))
        info.append(" f") if self.flash else None
        info.append(" rp") if self.red_point else None
        info = "".join(info)

        return self.grade + info if info else self.grade

@dataclass(frozen=True)
class Exercise:
    """Exercise in set of GPP/SFP training."""

    name: str
    repeats: tuple[int, ...]

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Invalid input: empty name")
        if not self.repeats or any(x <= 0 for x in self.repeats):
            raise ValueError(f"Invalid repeats: {self.repeats}")

    def __str__(self) -> str:
        repeats = REP_DELIMITER.join(str(n) for n in self.repeats)

        return f"{self.name} {repeats}"
