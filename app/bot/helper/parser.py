from app.bot.states.add_workout import FSMWorkoutDataComplete


class MessageParser:
    @classmethod
    def prettify_FSM_workout_data(cls, data: FSMWorkoutDataComplete) -> str:
        return (
            f"— {data['workout_date'].strftime("%d.%m.%Y")} ({data['training_type'].translator}) —\n"
            f"{data['content']}\n"
            f"Комментарии: {data['comments'] if data['comments'] != "-" else '(пусто)'}"
        )
