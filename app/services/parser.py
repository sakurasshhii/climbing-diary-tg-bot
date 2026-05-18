from app.domain.models import Workout, Row


class WorkoutParser:
    '''
    Workout parser to get info from user message.
    '''
    @staticmethod
    def parse_rows(text: str) -> list[Row]:
        return []