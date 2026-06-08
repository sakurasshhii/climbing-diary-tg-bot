from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domain.models import User
from app.infrastructure.database.repo import UserRepository
from app.infrastructure.database.sql_models import (GET_USER_BY_TG_ID,
                                                    INSERT_JOURNAL,
                                                    INSERT_USER)


class TestUserRepo:
    @pytest.mark.asyncio
    async def test_add_user(self, user_repo_db):
        await user_repo_db.add_user(123, "username")
        user_repo_db.db.execute.assert_awaited_once_with(
            INSERT_USER,
            (123, "username"),
        )

    @pytest.mark.asyncio
    async def test_get_user_by_tg_ok(self, user_repo_db):
        user_data = dict(
            id=1,
            tg_id=123,
            username="arina",
            last_journal=None,
        )
        user_repo_db.db.fetchone.return_value = user_data
        result = await user_repo_db.get_user_by_tg(123)
    
        user_repo_db.db.fetchone.assert_awaited_once_with(
            GET_USER_BY_TG_ID,
            (123,),
        )
        assert result == User(**user_data)

    @pytest.mark.asyncio
    async def test_get_user_by_tg_none(self, user_repo_db):
        user_data = None
        user_repo_db.db.fetchone.return_value = user_data
        result = await user_repo_db.get_user_by_tg(123)
    
        user_repo_db.db.fetchone.assert_awaited_once_with(
            GET_USER_BY_TG_ID,
            (123,),
        )
        assert result is None


class TestJournalRepo:
    @pytest.mark.asyncio
    async def test_add_journal(self, journal_repo_db):
        await journal_repo_db.add_journal(123)

        journal_repo_db.db.execute.assert_awaited_once_with(
            INSERT_JOURNAL,
            (123, "", "", None, None)
        )
    
    @pytest.mark.asyncio
    @patch("app.infrastructure.database.repo.Transaction")
    async def test_add_workout_no_journal(
        self,
        transaction_mock,
        journal_repo_db,
        workout_climb,
    ):
        db = journal_repo_db.db
        transaction_mock.return_value.__aenter__.return_value = db
        db.fetchone.return_value = None
        await journal_repo_db.add_workout(123, workout_climb)

        db.fetchone.assert_awaited_once()
        db.execute.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_add_workout(self):
        # TO DO
        pass

    @pytest.mark.asyncio
    async def test_get_journal_full_ok(self):
        # TO DO
        pass
