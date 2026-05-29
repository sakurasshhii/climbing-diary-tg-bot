import pytest


class TestUserService:
    @pytest.mark.asyncio
    async def test_add_user(self, user_service, user_repo):
        await user_service.add_user(
            123,
            "mikky",
        )
        user_repo.add_user.assert_awaited_once_with(
            tg_id=123,
            username="mikky",
        )

    @pytest.mark.asyncio
    async def test_get_user_ok(self, user_service, user_repo):
        user_repo.get_user_by_tg.return_value = {
            "id": 1,
            "tg_id": 123,
            "username": "mikky",
            "last_journal": 5,
        }
        user = await user_service.get_user(
            123
        )
        assert user.tg_id == 123
        assert user.username == "mikky"
