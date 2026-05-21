import datetime as dt
import re
from typing import Sequence
from app.domain.models import Workout, Row, Route, Exercise, GymTrain, ClimbTrain
from app.domain.enums import TrainingType, TrainingCategory


class JournalParser:
    '''
    Workout parser to get info from user message.
    '''
    @classmethod
    def is_valid_rows(cls, text: str, training_type: str) -> bool | Sequence[Row]:
        try:
            tr_type = TrainingCategory([training_type.upper()])
            rows = cls.parse_rows(text, tr_type)
        except ValueError as e:
            return False
        else:
            return rows

    @classmethod
    def parse_rows(cls, text: str, training_category: TrainingCategory) -> Sequence[Row]:
        '''Use to extract gum/climbing training rows(sets) from user's message. '''

        if training_category == TrainingCategory.CLIMBING:
            return cls.parse_rows_climbing(text)
        elif training_category == TrainingCategory.GYM:
            return cls.parse_rows_gym(text)
        else:
            raise TypeError(f'Incorrect trainig category: {training_category}')

    @classmethod
    def parse_rows_gym(cls, text: str) -> Sequence[Row]:
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

    @classmethod
    def parse_rows_climbing(cls, text: str) -> Sequence[Row]:
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

    @classmethod
    def get_route(cls, text: str) -> Route:
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

    @classmethod
    def parse_workout(cls, workout_date: dt.date, training_category: TrainingCategory,
            training_type: TrainingType, content: str, comments: str) -> Workout:
        ''' Use to create Workout from tg form. '''
        rows = list(cls.parse_rows(content, training_category=training_category))

        if training_category == TrainingCategory.CLIMBING:
            train = ClimbTrain(
                type=training_type, rows=rows, comments=comments)
        elif training_category == TrainingCategory.GYM:
            rows = list(cls.parse_rows_gym(content))
            train = GymTrain(
                type=training_type, rows=rows, comments=comments)
        else:
            raise ValueError(f'Incorrect trainig category: {training_category}')

        return Workout(
            date=workout_date, content=[train])
