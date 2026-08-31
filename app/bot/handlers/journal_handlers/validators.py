from aiogram.types import CallbackQuery, InaccessibleMessage, Message

from app.bot.handlers import exceptions as exc


def assure_message_from_user_id(message: Message) -> tuple[Message, int]:
    """Check if message has user info.
    
    Returns:
        message (Message): assured message;
        user id (int): user.id if exists.
    """

    if not message.from_user or not message.from_user.id:
        raise exc.NoInfoFromUserError(__name__)

    return message, message.from_user.id

def assure_callback_message(cback: CallbackQuery) -> Message:
    """Check if cback has user info and message; returns cback.message."""
    if not cback.from_user:
        raise exc.NoInfoFromUserError(__name__)
    if (
        cback.message is None
        or isinstance(cback.message, InaccessibleMessage)
        or not cback.message.from_user
        or not cback.message.from_user.id
    ):
        raise exc.MessageError(f'cback.message is None or isinstance(cback.message, InaccessibleMessage)')
    
    return cback.message

def assure_callback_data(cback: CallbackQuery, raise_err: bool = False) -> str:
    """Returns cback.data as str. Raises ValueError optionally."""
    if raise_err and not cback.data:
        raise ValueError("Missed cback.data")

    return cback.data or ""
