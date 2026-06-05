from enum import Enum


class TrainingType(Enum):
    LEAD = 'Lead'
    BOULDER = 'Boulder'
    GPP = 'GPP'
    SFP = 'SFP'

    @property
    def translator(self) -> str:
        tr_types = {
                TrainingType.LEAD: "Трудность",
                TrainingType.BOULDER: "Боулдер",
                TrainingType.GPP: "ОФП",
                TrainingType.SFP: "СФП",
        }
        return tr_types[self]


class TrainingCategory(Enum):
    CLIMBING = 'Climbing'
    GYM = 'Gym'
