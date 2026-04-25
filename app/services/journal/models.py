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

* — not necessarily arguments

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
from .exceptions import InvalidInputError
from .enums import TrainingType


class Journal:
    '''
    Great class contains multiple workout sessions.
    '''
    def __init__(self, content: list[Workout], comments: str | None = None) -> None:
        self._content = sorted(content, key=lambda x: x.date)
        self.comments = comments
        if len(content) > 0:
            self.period_st, self.period_en = [self._content[0].date, self._content[-1].date]

    @property
    def period(self):
        return (self.period_st, self.period_en)
    
    def __str__(self) -> str:
        date = f'[{"-".join(map(str, self.period))}]\n'
        about = f'About this journal: {self.comments}\n' if self.comments else ''
        return date + about + '\n ——— \n'.join(x.__str__() for x in self._content)


class Workout:
    '''
    One workout session a day.
    It could contain several training types inside.
    '''
    def __init__(self, date: dt.date, content: list[Train], comments: str | None = None) -> None:
        self.date = date
        self._content = list(content)
        self.comments = comments
    
    def __len__(self):
        return len(self._content)
    
    def __str__(self) -> str:
        return '\n'.join([
            f'Date: {self.date.isoformat()}',
            *(x.__str__() for x in self._content)
        ])

        
class Train:
    '''
    Group of she same type of physical activity.
    Used as parent for climbing/not climbing.
    '''
    def __init_subclass__(cls, train_type) -> type:
        cls.train_type = train_type
        return cls
    
    def __init__(self, type: TrainingType, sets: list[Set], comments: str | None = None) -> None:
        self._type = type
        self._sets = list(sets)
        self.comments = comments
    
    def __str__(self) -> str:
        return f'{self._type.name.capitalize()}:\n{"\n".join(x.__str__() for x in self._sets)}' \
            f'{'\nComments: ' + self.comments if self.comments else ''}'


class ClimbTrain(Train, train_type='Climb'):
    pass


class GymTrain(Train, train_type='Gym'):
    pass


@dataclass(frozen=True)
class Set:
    '''
    Container used to group activity in one training set.
    '''
    content: list[Route | Exercise]
    comments: str | None = None

    def __post_init__(self) -> None:
        if not len(self.content):
            raise ValueError('Empty set is not avaiable.')
    
    def __str__(self) -> str:
        return ' | '.join((x.__str__() for x in self.content)) + \
            f'{'; comments: ' + self.comments if self.comments else ''}'


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
        '''
        Exercise format: {name};{repeats}

        name — name of the exercise
        repeats — looks like 1-2-3 where number means repetitions in one set
        '''
        if not self.name:
            raise ValueError('Invalid input: empty name')
        if not len(self.repeats) or any(x <= 0 for x in self.repeats):
            raise ValueError(f'Invalid repeats: {self.repeats}')
    
    @classmethod
    def from_str(cls, string: str) -> Exercise:
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
