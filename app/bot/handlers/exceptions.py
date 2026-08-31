class NoInfoFromUserError(Exception):
    ''' Can't get user_id from Message / CallbackQuery'''
    def __init__(self, name: str) -> None:
        self.name = name

class MessageError(Exception):
    ''' Errors with cback.message '''
    def __init__(self, text: str) -> None:
        self.text = text

class JournalError(Exception):
    ''' Errors with journal '''
    def __init__(self, text: str) -> None:
        self.text = text

class InvalidDateError(JournalError):
    def __init__(self, date) -> None:
        self.date = date
    
    def __str__(self) -> str:
        return f'Date must be in ISO format: YYYY-MM-DD: {self.date}'