import pytest
from unittest.mock import AsyncMock

from app.bot.handlers.commands import (
    process_start_command, process_help_command, process_cancel_command,
    undefined_message, undefined_cback)
from app.lexic.ru import MAIN_MENU_MSG, UNDEFINED


class TestCommands:
    @pytest.mark.asyncio
    async def test_proc_start_cmd(self, message, user_service_empty):
        await process_start_command(message, user_service_empty)
        user_service_empty.add_user.assert_awaited_once_with(
            message.from_user.id,
            message.from_user.username,
        )
        message.answer.assert_awaited_once_with(
            text=MAIN_MENU_MSG["/start"]
        )

    @pytest.mark.asyncio
    async def test_proc_start_no_user(self, message_empty, user_service_empty):
        message_empty.from_user = None
        await process_start_command(message_empty, user_service_empty)

        user_service_empty.add_user.assert_not_awaited()
        message_empty.answer.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_proc_help_cmd(self, message, user_service_empty):
        user_service_empty.get_user_assured.return_value = {"id": 1}
        await process_help_command(message, user_service_empty)

        user_service_empty.get_user_assured.assert_awaited_once_with(
            message.from_user.id
        )
        message.answer.assert_awaited_once_with(MAIN_MENU_MSG["/help"])

    @pytest.mark.asyncio
    async def test_proc_cancel_cmd(self, message, state):
        state.get_state.return_value = ("AddWorkout:content")
        await process_cancel_command(message, state)

        state.get_state.assert_awaited_once()
        state.clear.assert_awaited_once()
        message.answer.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_undefined_msg(self, message):
        await undefined_message(message)

        message.answer.assert_awaited_once_with(text=UNDEFINED["message"])

    @pytest.mark.asyncio
    async def test_undefined_callback(self, state, cback_empty):
        cback_empty.data = "some_data"
        state.get_state.return_value = "AnyState"
        await undefined_cback(cback_empty, state)

        cback_empty.message.answer.assert_awaited_once_with(
            text=UNDEFINED["callback"]
        )
