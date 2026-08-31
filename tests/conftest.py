from __future__ import annotations

import datetime as dt
from collections.abc import Sequence
from unittest.mock import AsyncMock

import pytest

from app.domain.enums import TrainingCategory, TrainingType
from app.domain.models import (ClimbTrain, Exercise, GymTrain, Journal, Route,
                               Row, User, Workout)
from app.infrastructure.database.repo import JournalRepository, UserRepository
from app.services.services import JournalService, UserService


# —————————————————————————— DB models —————————————————————————
@pytest.fixture
def default_user() -> User:
    return User(**{
            "id": 1,
            "tg_id": 123,
            "username": "arina",
            "last_journal": None,
        })

# —————————————————————————— models ————————————————————————————
@pytest.fixture
def new_date() -> dt.date:
    return dt.datetime.now().date()

@pytest.fixture
def route() -> Route:
    return Route(grade='6a', falls_no=0, flash=False)

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
def workout_climb(train_climb_fill, new_date) -> Workout:
    return Workout(date=new_date, content=[train_climb_fill])

@pytest.fixture
def workout_gym(train_gym_fill, new_date) -> Workout:
    return Workout(date=new_date, content=[train_gym_fill])

# —————————————————————————— AsyncMock ————————————————————————————
@pytest.fixture
def db_mock():
    return AsyncMock()

@pytest.fixture
def user_repo():
    return AsyncMock()

@pytest.fixture
def user_repo_db(db_mock):
    return UserRepository(db_mock)

@pytest.fixture
def journal_repo():
    return AsyncMock()

@pytest.fixture
def journal_repo_db(db_mock):
    return JournalRepository(db_mock)

@pytest.fixture
def user_service_empty():
    return AsyncMock()

@pytest.fixture
def user_service(user_repo):
    return UserService(user_repo)

@pytest.fixture
def journal_service(user_repo, journal_repo):
    return JournalService(
        user_repo,
        journal_repo,
    )

@pytest.fixture
def message_empty():
    return AsyncMock()

@pytest.fixture
def message(message_empty):
    message_empty.from_user.id = 123
    message_empty.from_user.username = "my_name"
    message_empty.text = "abc abc"

    return message_empty

@pytest.fixture
def cback_empty():
    return AsyncMock()

@pytest.fixture
def state():
    return AsyncMock()
