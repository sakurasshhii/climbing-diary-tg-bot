import datetime as dt
from unittest.mock import patch

import pytest

from app.domain.enums import TrainingCategory, TrainingType
from app.domain.exceptions import UserNotFoundError
from app.domain.models import DBJournal, Journal, User
from app.services.services import JournalService


class TestUserService:
    @pytest.mark.asyncio
    async def test_add_user(self, user_service, user_repo):
        await user_service.add_user(123, "mikky")
        user_repo.add_user.assert_awaited_once_with(
            tg_id=123,
            username="mikky",
        )

    @pytest.mark.asyncio
    async def test_get_user_ok(self, user_service, user_repo, default_user):
        user_repo.get_user_by_tg.return_value = default_user
        user = await user_service.get_user(123)

        assert user == default_user

    @pytest.mark.asyncio
    async def test_get_user_none(self, user_service, user_repo):
        user_repo.get_user_by_tg.return_value = None
        result = await user_service.get_user(123)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_user_assured_exists(self, user_service, user_repo, default_user):
        user_repo.get_user_by_tg.return_value = default_user
        user = await user_service.get_user_assured(default_user.tg_id)

        assert user == default_user
        user_repo.add_user.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_user_assured_create(self, user_service, user_repo, default_user):
        user_repo.get_user_by_tg.side_effect = [None, default_user]
        user = await user_service.get_user_assured(123, "one")

        user_repo.add_user.assert_awaited_once()
        assert user.tg_id == 123

class TestJournalService:
    @pytest.mark.asyncio
    async def test_add_journal_ok(
        self,
        journal_service,
        user_repo,
        journal_repo,
        default_user
    ):
        user_repo.get_user_by_tg.return_value = default_user
        await journal_service.add_journal(default_user.id)

        journal_repo.add_journal.assert_awaited_once_with(
            user_id=default_user.id,
            name="",
            comments="",
        )

    @pytest.mark.asyncio
    async def test_add_journal_user_missing(self, journal_service, user_repo):
        user_repo.get_user_by_tg.return_value = None

        with pytest.raises(UserNotFoundError):
            await journal_service.add_journal(123)

    @pytest.mark.asyncio
    @patch("app.services.services.JournalParser.parse_workout")
    async def test_add_workout_ok(
        self,
        parser_mock,
        user_repo,
        journal_repo,
        journal_service,
    ):
        user_repo.get_user_by_tg.return_value = {"id": 1}
        fake_workout = object()
        parser_mock.return_value = fake_workout

        data = {
            "workout_date": dt.date.today(),
            "training_category": TrainingCategory.CLIMBING,
            "training_type": TrainingType.LEAD,
            "content": "6a",
            "comments": "",
            "journal_no": 5,
        }

        await journal_service.add_workout(123, data)

        parser_mock.assert_called_once()
        journal_repo.add_workout.assert_awaited_once_with(
            journal_id=5,
            workout=fake_workout,
        )

    @pytest.mark.asyncio
    async def test_add_workout_user_not_found(self, user_repo, journal_service):
        user_repo.get_user_by_tg.return_value = None

        with pytest.raises(UserNotFoundError):
            await journal_service.add_workout(123, {})

    @pytest.mark.asyncio
    async def test_get_journals_ok(
        self,
        user_repo,
        journal_repo,
        journal_service,
        default_user,
    ):
        user_repo.get_user_by_tg.return_value = default_user
        expected = ["j1", "j2"]
        journal_repo.get_journals.return_value = (expected)

        result = await journal_service.get_journals(default_user.id)

        assert result == expected
        journal_repo.get_journals.assert_awaited_once_with(default_user.id)

    @pytest.mark.asyncio
    async def test_get_journals_user_not_found(self, user_repo, journal_service):
        user_repo.get_user_by_tg.return_value = None

        with pytest.raises(UserNotFoundError):
            await journal_service.get_journals(123)

    @pytest.mark.asyncio
    async def test_get_complete_journal_not_found(self, journal_repo, journal_service):
        journal_repo.get_journal_full.return_value = None

        with pytest.raises(ValueError, match="Journal not found"):
            await journal_service.get_complete_journal(1)

    @pytest.mark.asyncio
    async def test_get_complete_journal_ok(
        self,
        journal_repo,
        journal_service,
        workout_climb
    ) -> None:
        journal_repo.get_journal_full.return_value = Journal(
            content=[workout_climb, workout_climb],
            comments="my comment"
        )

        result = await journal_service.get_complete_journal(1)

        assert isinstance(result, Journal)
        assert len(result) == 2
        assert result.comments == "my comment"

    def test_training_validation_true(self):
        result = JournalService.training_sets_validation(
            "6a",
            TrainingCategory.CLIMBING,
        )
        assert result is True

    def test_training_validation_false(self):
        result = JournalService.training_sets_validation(
            " ",
            TrainingCategory.GYM,
        )
        assert result is False
