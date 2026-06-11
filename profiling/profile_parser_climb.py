from app.domain.enums import TrainingCategory
from app.services.parser import JournalParser

TEXT_CLIMBING = "6a, 6a+, 6b:, 6b+ f, 6c rp - my routes\n" * 100_000

def scenario():
    parser = JournalParser()
    parser.parse_rows(TEXT_CLIMBING, training_category=TrainingCategory.CLIMBING)


if __name__ == "__main__":
    scenario()
