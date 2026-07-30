class UserNotFoundError(Exception):
    def __init__(self, user_id) -> None:
        self.user_id = user_id


class JournalNotFoundError(Exception):
    def __init__(self, journal_id) -> None:
        self.journal_id = journal_id

    def __str__(self) -> str:
        return "Journal not found: " + self.journal_id


class WorkoutError(Exception):
    def __init__(self, txt) -> None:
        self.txt = txt

    def __str__(self) -> str:
        return "Error while DB process: " + self.txt
