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

<<<<<<< HEAD

=======
>>>>>>> fef7848d8f5855871c4906a23f233dd9f64493a1
class TrainingCategory(Enum):
    CLIMBING = 'Climbing'
    GYM = 'Gym'
