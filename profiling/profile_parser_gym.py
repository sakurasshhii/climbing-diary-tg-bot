from app.domain.enums import TrainingCategory
from app.services.parser import JournalParser

TEXT_GYM = "pull-ups - 10/10/10 - my exercises\n" * 100_000

def scenario():
    JournalParser.parse_rows(TEXT_GYM, training_category=TrainingCategory.GYM)


if __name__ == "__main__":
    scenario()
