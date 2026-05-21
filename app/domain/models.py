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
            sets: [Row([Route(rate[str], falls[int], flash[int]), ...], *comments), ...],
        ),
        GymTrain(
            type: GPP | SFP,
            sets: [Row([Exercise(name[str], repeats), ...], *comments), ...],
        )
    ],
    *comments: str | None = None
)

* - not necessarily arguments

***
В базовой реализации (сейчас):
Exercise всегда существует в Set в одном экземпляре, внутри которого уазан repeats.
То есть, весь Set записан в одном упражнении. (len(Set) == 1)
***
Расширение на будующее:
exercise_sets — вместо хранения повторений в json / списке
├── exercise_id
├── weight
├── reps
├── order
'''
from __future__ import annotations

import re
import datetime as dt

from dataclasses import dataclass, field
from typing import Sequence
from .enums import TrainingType, TrainingCategory


################################## User ####################################

@dataclass
class User:
    id: int
    tg_id: int
    username: str
    last_journal: int

################################## Journal #################################

@dataclass
class Journal:
    '''
    Great class contains multiple workout sessions.
    '''
    content: list[Workout] = field(default_factory=list)
    comments: str = ''

    def __post_init__(self):
        if self.content:
            if not all(isinstance(x, Workout) for x in self.content):
                raise TypeError('Journal must contain Workout objects only.')
            self.content.sort(key=lambda x: x.date)

    @property
    def period(self) -> tuple[dt.date | None, dt.date | None]:
        if self.content:
            return (self.content[0].date, self.content[-1].date)
        return (None, None)

    def add_workout(self, workout: Workout):
        if isinstance (workout, Workout):
            self.content.append(workout)
            if len(self) >=2 and self.content[-2].date > workout.date:
                self.content.sort(key=lambda x: x.date)
        else:
            raise TypeError('Journal could contain Workout objects only.')

    def __str__(self) -> str:
        if not self.content:
            return 'Empty journal.'
        date = f'[{"-".join(map(str, self.period))}]\n'
        about = f'About this journal: {self.comments}\n' if self.comments else ''
        return date + about + '\n ——— \n'.join(x.__str__() for x in self.content)
    
    def __len__(self):
        return len(self.content)


@dataclass
class Workout:
    '''
    One workout session a day.
    It could contain several training types inside.
    '''
    date: dt.date
    content: list[Train] = field(default_factory=list)
    comments: str = ''

    def add_train(self, train: Train):
        if isinstance(train, Train):
            self.content.append(train)
        else:
            raise TypeError('Workout could contain Train objects only.')
    
    @property
    def get_content(self) -> Sequence[Train]:
        return tuple(self.content)

    def __str__(self) -> str:
        if not self.content:
            return f'Date: {self.date.isoformat()}; no trainings yet.'
        return '\n'.join([
            f'Date: {self.date.isoformat()};',
            *(x.__str__() for x in self.content)
        ])


@dataclass
class Train:
    '''
    Group of the same type of physical activity.
    Used as parent for climbing/not climbing.
    '''
    training_category: TrainingCategory = field(init=False)
    type: TrainingType
    rows: list[Row]
    comments: str = ''

    @property
    def get_rows(self) -> Sequence[Row]:
        return tuple(self.rows)

    def add_row(self, row: Row):
        if isinstance(row, Row):
            self.rows.append(row)
        else:
            raise TypeError('Train could contain Row objects only.')

    def __str__(self) -> str:
        if not self.rows:
            return f'{self.type.name}: empty training.'

        comments = f'\nComments: {self.comments}' if self.comments else ''
        rows = '\n'.join(str(x) for x in self.rows)

        return f'{self.type.name}:\n{rows}{comments}'


@dataclass
class ClimbTrain(Train):
    training_category = TrainingCategory.CLIMBING


@dataclass
class GymTrain(Train):
    training_category = TrainingCategory.GYM


@dataclass(frozen=True)
class Row:
    '''
    Container used to group activity in one training set.
    '''
    content: tuple[Route | Exercise, ...]
    comments: str = ''

    def __post_init__(self) -> None:
        if not len(self.content):
            raise ValueError('Empty set is not avaiable.')
    
    @property
    def get_content(self) -> Sequence[Route | Exercise]:
        return tuple(self.content)

    def __str__(self) -> str:
        content = ' | '.join((x.__str__() for x in self.content))
        comments = f' ({self.comments})' if self.comments else ''
        return content + comments

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
        if not re.fullmatch(r'\d[abcABC]\+?', self.grade):
            raise ValueError(f'Invalid grade: {self.grade}')
        if not isinstance(self.falls, int) or self.falls < 0:
            raise ValueError(f'Invalid falls count: {self.falls}')
        if not isinstance(self.flash, bool) or self.flash and self.falls:
            raise ValueError(f'Invalid flash flag: {self.flash}')

    def __str__(self) -> str:
        return f"{self.grade}{'(fall)' if self.falls else ''}{'(flash)' if self.flash else ''}"


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
        if not self.repeats or any(x <= 0 for x in self.repeats):
            raise ValueError(f'Invalid repeats: {self.repeats}')

    def __str__(self) -> str:
        return f"{self.name};{'|'.join(map(str, self.repeats))}"
