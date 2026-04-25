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


class Set:
    '''
    Container used to group activity in one training set.
    '''
    def __init__(self, content: list[Route | Exercise], comments: str | None = None) -> None:
        self._content = list(content)
        self.comments = comments
    
    def __str__(self) -> str:
        return ' | '.join((x.__str__() for x in self._content)) + \
            f'{'; comments: ' + self.comments if self.comments else ''}'


class Route:
    '''
    Route rate via French/Fontainebleau system.
    '''
    def __init__(self, route: str) -> None:
        '''
        Route format: {grade}{:falls}{f if flash}

        grade — French grade from 5a to 9b+
        falls — count of falls in route before top
        flash — if route was climbed first time and without falls
        '''
        match = re.fullmatch(r'(\d[abc]\+?)(:?)(f?)', route)
        if match is None:
            raise InvalidInputError(route) from ValueError
        
        rate, is_climbed, is_flash = match.groups()
        self._route = {
        }
        self.rate = rate
        self.falls = int(is_climbed == ':')
        if self.falls > 0:
            self.flash = False
        else:
            self.flash = is_flash == 'f'
    
    def __str__(self) -> str:
        return f'{self.rate}{'(fall)' if self.falls else ''}{'(flash)' if self.flash else ''}'
        

class Exercise:
    '''
    Exercise in set of GPP/SFP training
    '''
    def __init__(self, exercise: str) -> None:
        '''
        Exercise format: {name};{repeats}

        name — name of the exercise
        repeats — looks like 1-2-3 where number means repetitions in one set
        '''
        match = re.fullmatch(r'(\D+);(\d+[\d-]*)', exercise)
        if match is None:
            raise InvalidInputError(exercise) from ValueError
        
        name, rep = match.groups()
        self.name = name.strip()
        self.repeats =  tuple(map(int, rep.split('-')))

    def __str__(self) -> str:
        return f'{self.name}: {"|".join(map(str, self.repeats))}'
