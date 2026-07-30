from app.bot.states.add_workout import FSMWorkoutDataComplete
from app.services.services import JournalService


class MessageParser:
    @classmethod
    def prettify_FSM_workout_data(
        cls,
        data: FSMWorkoutDataComplete,
        journal_service: JournalService
    ) -> str:
        """Get readable workout preview format before adding it to DB."""
        sets = journal_service.parser.loads_sets(data['content'], data['training_category'])
        preview = "\n".join(str(s) for s in sets)
        
        return (
                f"— {data['workout_date'].strftime("%d.%m.%Y")} ({data['training_type'].translator}) —\n"
                f"{preview}\n"
                f"Комментарии: {data['comments'] if data['comments'] != "-" else '(пусто)'}"
            )
