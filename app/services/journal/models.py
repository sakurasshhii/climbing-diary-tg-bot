'''
Классы, формирующие тренировочный журнал длительностью один тренировочный цикл.

***
Structure:

Journal(
    content: list = [Workout(), ...],        # all trainings in training cycle
    period: tuple[dt.date, dt.date],         # start & end date — property
    comments: str | None = None,             # comments to the whole journal
)
Workout(
    date: dt.date,
    content: list[Train] = [
        ClimbTrain(
            type: lead | boulder,
            sets: [Set([Route(rate[str], falls[int], flash[int]), ...], *comments), ...],
        ),
        GymTrain(
            type: GPP | SFP,
            sets: [Set([Exercise(name[str], repeats), ...], *comments), ...],
        )
    ],
    *comments: str | None = None
)

* - not necessarily arguments

***
Логика сбора в Set для Exercise:
Если repeats == 1-1-1 (несколько через дефис) — автоматом разбиваются и создается сет
Если repeats == 1 — добавляем в Set по аналогии с Route (поддержка круговой тренировки)

В базовой реализации (сейчас):
Exercise всегда существует в Set в одном экземпляре, внутри которого уазан repeats.
То есть, весь Set записан в одном упражнении. (len(Set) == 1)
'''

import re
import datetime as dt

from dataclasses import dataclass
# from collections.abc import Collection
# from .exceptions import InvalidInputError
from .enums import TrainingType


##################### body #####################

# is this @dataclass? -> comments as property
class Journal:
    '''
    Great class contains multiple workout sessions.
    '''
    def __init__(self, content: list[Workout] | None = None, comments: str | None = None) -> None:
        self._content = content
        if self._content:
            self._content.sort(key=lambda x: x.date)
        self.comments = comments

    @property
    def period(self) -> tuple[dt.date | None, dt.date | None]:
        if self._content:
            return (self._content[0].date, self._content[-1].date)
        return (None, None)

    @property
    def comments(self):
        return self._comments

    @comments.setter
    def comments(self, val):
        if not (val is None or isinstance(val, str)):
            raise ValueError(f'Invalid input for comments: {val}')
        if not hasattr(self, '_comments') or self._comments is None:
            self._comments = val
        else:
            self._comments += '; ' + val

    @comments.deleter
    def comments(self):
        self._comments = None

    def add_workout(self, workout: Workout):
        if self._content is None:
            self._content = [workout, ]
        else:
            self._content.append(workout)
            if self._content[-2].date > workout.date:
                self._content.sort(key=lambda x: x.date)

    def __str__(self) -> str:
        if self._content is None:
            return 'Empty journal...'
        date = f'[{"-".join(map(str, self.period))}]\n'
        about = f'About this journal: {self.comments}\n' if self.comments else ''
        return date + about + '\n ——— \n'.join(x.__str__() for x in self._content)


@dataclass  # (frozen=True)
class Workout:
    '''
    One workout session a day.
    It could contain several training types inside.
    '''
    date: dt.date
    content: list[Train] | None = None
    comments: str | None = None

    def add_train(self, training: Train, comments: str = '') -> None:
        if self.content is None:
            self.content = []
        self.content.append(training)
        if comments and self.comments:
            self.comments += '; ' + comments
        else:
            self.comments = comments

    def __len__(self):
        return len(self.content) if self.content else None

    def __str__(self) -> str:
        if self.content is None:
            return f'Date: {self.date.isoformat()}; no trainings yet.'
        return '\n'.join([
            f'Date: {self.date.isoformat()}',
            *(x.__str__() for x in self.content)
        ])


class Train:
    '''
    Group of she same type of physical activity.
    Used as parent for climbing/not climbing.
    '''
    def __init_subclass__(cls, train_type) -> type:
        cls.train_type = train_type
        return cls

    def __init__(self,
                type: TrainingType,
                sets: list[Row] | None = None,
                comments: str | None = None
        ) -> None:
        self._type = type
        self._sets = list(sets) if sets else None
        self.comments = comments

    def add_set(self, tr_set: Row, comments: str = ''):
        if self._sets is None:
            self._sets = []
        self._sets.append(tr_set)
        if comments and self.comments:
            self.comments += '; ' + comments
        else:
            self.comments = comments

    def __str__(self) -> str:
        if self._sets is None:
            return f'{self._type.name}: empty training.'
        return f'{self._type.name}:\n{"\n".join(x.__str__() for x in self._sets)}' \
            f'{'\nComments: ' + self.comments if self.comments else ''}'


class ClimbTrain(Train, train_type='Climb'):
    pass


class GymTrain(Train, train_type='Gym'):
    pass


@dataclass(frozen=True)
class Row:
    '''
    Container used to group activity in one training set.
    '''
    content: list  # [Route | Exercise]
    comments: str | None = None

    def __post_init__(self) -> None:
        if not len(self.content):
            raise ValueError('Empty set is not avaiable.')

    def __str__(self) -> str:
        return ' | '.join((x.__str__() for x in self.content)) + \
            f'{'; comments: ' + self.comments if self.comments else ''}'

    @classmethod
    def from_user_str(cls, raw: str, type: TrainingType, delimiter: str = '-') -> Row:
        '''
        Create Set from string.
        - Climbing -
            temp: '{Route} {Route} {...} {comments}'
            example: '6a 6a+ 6b: light warm-up'
        - Gym (GPP/SFP) -
            temp: '{exercise_name} {rep1}-{rep2}-{...} {comments}'
            example: 'push-up 5-8-8 harder then yesterday'
        '''
        match type:
            case TrainingType.GPP | TrainingType.SFP:
                s = cls.stack_exercise(raw, delimiter=delimiter)
                return Row(**s)
            case TrainingType.LEAD | TrainingType.BOULDER:
                s = cls.stack_routes(raw)
                print(s)
                return Row(**s)

    @staticmethod
    def stack_routes(raw: str) -> dict:
        routes = []
        comments = []
        wait_for_comment = False
        for elm in raw.split():
            if not wait_for_comment:
                try:
                    r = Route.from_str(elm)
                except ValueError:
                    wait_for_comment = True
                else:
                    routes.append(r)
            else:
                comments.append(elm)

        return {'content': routes, 'comments': ' '.join(comments)}

    @staticmethod
    def stack_exercise(raw: str, delimiter: str = '-') -> dict:
        # new method instead of Exercise.from_str() - because of comments
        name = []
        repeats = []
        comments = []
        wait_for_comment = False

        for elm in raw.split():
            if not wait_for_comment:
                if re.fullmatch(r'\D*', elm):
                    name.append(elm)
                else:
                    repeats = list(map(int, elm.split(delimiter)))
                    wait_for_comment = True
            else:
                comments.append(elm)

        ex = Exercise(
            name=' '.join(name),
            repeats=tuple(repeats)
        )
        return {'content': [ex, ], 'comments': ' '.join(comments)}


################## inner layer of composition: Route & Exercise ##################

@dataclass(frozen=True)
class Route:
    '''
    Route rate via French/Fontainebleau system.
    '''
    grade: str
    falls: int = 0
    flash: bool = False

    def __post_init__(self) -> None:
        '''
        Route format: {grade}{:falls}{f if flash}

        grade — French grade from 5a to 9b+
        falls — count of falls in route before top
        flash — if route was climbed first time and without falls
        '''
        if not re.fullmatch(r'\d[abc]\+?', self.grade):
            raise ValueError(f'Invalid grade: {self.grade}')
        if not isinstance(self.falls, int) or self.falls < 0:
            raise ValueError(f'Invalid falls count: {self.falls}')
        if not isinstance(self.flash, bool) or self.flash and self.falls:
            raise ValueError(f'Invalid flash flag: {self.flash}')

    @classmethod
    def from_str(cls, string: str) -> Route:
        match = re.fullmatch(r'(\d[abc]\+?)(:?)(f?)', string)
        if match is None:
            raise ValueError(f'Invalid input: {string}')

        grade, is_climbed, is_flash = match.groups()
        falls = int(is_climbed == ':')
        if falls > 0:
            flash = False
        else:
            flash = is_flash == 'f'

        return cls(grade, falls, flash)

    def __str__(self) -> str:
        return f'{self.grade}{'(fall)' if self.falls else ''}{'(flash)' if self.flash else ''}'


@dataclass(frozen=True)
class Exercise:
    '''
    Exercise in set of GPP/SFP training
    '''
    name: str
    repeats: tuple[int, ...]
    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError('Invalid input: empty name')
        if not len(self.repeats) or any(x <= 0 for x in self.repeats):
            raise ValueError(f'Invalid repeats: {self.repeats}')

    @classmethod
    def from_str(cls, string: str) -> Exercise:
        '''
        Exercise format: {name};{repeats}

        name — name of the exercise
        repeats — looks like 1-2-3 where number means repetitions in one set
        '''
        match = re.fullmatch(r'(\D+);(\d+[\d-]*)', string)
        if match is None:
            raise ValueError(f'Invalid input: {string}')
        name, rep = match.groups()

        return Exercise(
            name.strip(),
            tuple(map(int, rep.split('-')))
            )

    def __str__(self) -> str:
        return f'{self.name};{"|".join(map(str, self.repeats))}'
