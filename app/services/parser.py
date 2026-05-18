import datetime as dt
import re
from typing import Sequence
from app.domain.models import Workout, Row, Route, Exercise, GymTrain, ClimbTrain
from app.domain.enums import TrainingType


class JournalParser:
    '''
    Workout parser to get info from user message.
    '''
    @staticmethod
    def is_valid_rows(text: str, training_type: str) -> bool | Sequence[Row]:
        try:
            if training_type == 'climb_train':
                result = JournalParser.parse_rows_climb(text)
            else:
                result = JournalParser.parse_rows_gym(text)
        except ValueError as e:
            return False
        else:
            return result

    @staticmethod
    def parse_rows_gym(text: str) -> Sequence[Row]:
        ''' Use to extract gym training rows from user's message. '''
        
        rows = []

        for row in text.split('\n'):
            match = re.fullmatch(r'(?P<name>[\w\s]+)\s(?P<repeats>[\d/]+)/?\s?(?P<comments>.+)?', row)
            if not match:
                return []
            repeats = match['repeats'].strip('/').split('/')
            repeats = tuple(map(int, repeats))
            exercise = Exercise(name=match['name'], repeats=repeats)
            comments = match['comments']
            rows.append(Row(content=[exercise], comments=comments))

        return rows

    @staticmethod
    def parse_rows_climb(text: str) -> Sequence[Row]:
        ''' Use to extract climbing training rows from user's message. '''

        rows = []
        for line in text.split('\n'):
            routes, comments = [], ''
            for elm in line.split('/'):
                try:
                    routes.append(JournalParser.get_route(elm))
                except ValueError:
                    comments = elm
            if not routes:
                return []

            rows.append(Row(content=routes, comments=comments))

        return rows

    @staticmethod
    def get_route(text: str) -> Route:
        ''' Use to extract Route from user's message. '''

        match = re.fullmatch(r'(?P<grade>\d[abcабс]\+?)(?P<falls>\s\d)?', text)
        if not match or match['grade'] is None:
            raise ValueError('Incorrent climbing grade.')

        flash = False
        grade, falls = [m.strip() if m else False for m in match.groups()]
        assert isinstance(grade, str)
        for old, new in zip('абс', 'abc'):
            grade = grade.replace(old, new)
        if falls == '0':
            flash = True
        elif not falls:
            falls = 0

        return Route(grade=grade, falls=int(falls), flash=flash)

    def parse_workout(self, workout_date: dt.date, training_type: str,
            content: str, comments: str) -> Workout:
        
        tr_type = TrainingType[training_type.upper()]
        if tr_type in [TrainingType.LEAD, TrainingType.BOULDER]:
            rows = self.parse_rows_climb(content)
            train = ClimbTrain(
                type=tr_type, sets=rows, comments=comments)
        else:
            rows = self.parse_rows_gym(content)
            train = GymTrain(
                type=tr_type, sets=rows, comments=comments)
        
        return Workout(
            date=workout_date, content=[train])