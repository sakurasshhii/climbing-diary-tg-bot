from aiogram.types import CallbackQuery, InaccessibleMessage, Message

from app.bot.handlers import exceptions as exc


def assure_message_from_user_id(message: Message) -> Message:
    if not message.from_user or not message.from_user.id:
        raise exc.NoInfoFromUserError(__name__)
    
    return message

def assure_callback_message(cback: CallbackQuery) -> Message:
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