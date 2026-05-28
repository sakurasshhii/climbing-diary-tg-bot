from __future__ import annotations

import datetime as dt
from collections.abc import Sequence

import pytest
from app.domain.models import (
    Journal,
    Workout,
    GymTrain,
    ClimbTrain,
    Row,
    Route,
    Exercise,
)
from app.domain.enums import (
    TrainingCategory,
    TrainingType
)

DATE = dt.datetime.now().date()


@pytest.fixture
def route() -> Route:
    return Route(grade='6a', falls=0, flash=False)


@pytest.fixture
def exercise() -> Exercise:
    return Exercise(name='Ex 1', repeats=(1, 2, 3))


@pytest.fixture
def routes(route, n=3) -> Sequence[Route]:
    return (route,) * n


@pytest.fixture
def exercises(exercise, n=3) -> Sequence[Exercise]:
    return (exercise,) * n


@pytest.fixture
def row_routes(routes) -> Row:
    return Row(content=routes)


@pytest.fixture
def row_exercises(exercises) -> Row:
    return Row(content=exercises)

@pytest.fixture
def train_climb_empty() -> ClimbTrain:
    return ClimbTrain(type=TrainingType.LEAD)

@pytest.fixture
def train_climb_fill(row_routes, n=3) -> ClimbTrain:
    return ClimbTrain(type=TrainingType.LEAD, rows=[row_routes for _ in range(n)])

@pytest.fixture
def train_gym_empty() -> GymTrain:
    return GymTrain(type=TrainingType.GPP)

@pytest.fixture
def train_gym_fill(row_exercises, n=3) -> GymTrain:
    return GymTrain(type=TrainingType.GPP, rows=[row_exercises for _ in range(n)])

@pytest.fixture
def workout_climb(train_climb_fill) -> Workout:
    return Workout(date=DATE, content=[train_climb_fill])

@pytest.fixture
def workout_gym(train_gym_fill) -> Workout:
    return Workout(date=DATE, content=[train_gym_fill])