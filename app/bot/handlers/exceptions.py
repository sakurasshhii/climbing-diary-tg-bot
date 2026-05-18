class NoInfoFromUserError(Exception):
    '''can't get user_id from Message / CallbackQuery'''
    def __init__(self, name: str) -> None:
        self.name = name

class JournalError(Exception):
    pass

class InvalidDateError(JournalError):
    def __init__(self, date) -> None:
        self.date = date
    
    def __str__(self) -> str:
        return f'Date must be in ISO format: YYYY-MM-DD: {self.date}'