import datetime as dt
import pytest
from app.domain.models import (
    Journal,
    Workout,
    GymTrain,
    ClimbTrain,
    Row,
    Route,
    Exercise,
)
from app.domain.enums import (
    TrainingCategory,
    TrainingType
)
import app.domain.exceptions as exc


class TestExercise:
    def test_exercise_creation(self):
        assert Exercise(name='Ex 1', repeats=(1, 2, 3))

    def test__name_err(self):
        with pytest.raises(ValueError):
            Exercise(name='', repeats=(1, 2, 3))

    def test__repeats_err(self):
        with pytest.raises(ValueError):
            Exercise(name='Ex 1', repeats=(-1, 1, 1))


class TestRoute:
    def test_route_creation(self):
        assert Route(grade='6a', falls=0, flash=False)

    @pytest.mark.parametrize(
        'grade',
        ['6d', '6', '10a']
    )
    def test_grade_err(self, grade):
        with pytest.raises(ValueError):
            Route(grade=grade, falls=0, flash=False)

    def test_falls_err(self):
        with pytest.raises(ValueError):
            Route(grade='6a', falls=-1, flash=False)

    def test_flash_err(self):
        with pytest.raises(ValueError):
            Route(grade='6a', falls=1, flash=True)


class TestRow:
    def test_row_creation(self, exercises, routes):
        assert Row(content=exercises)
        assert Row(content=routes)
        assert Row(content=routes, comments='abc')

    def test_content_err(self):
        with pytest.raises(ValueError):
            Row(content=())

    @pytest.mark.parametrize(
        'fix_name,training_cat',
        [
            ('exercises', TrainingCategory.GYM),
            ('routes', TrainingCategory.CLIMBING),
        ]
    )
    def test_trainig_cat(self, request, fix_name, training_cat):
        content = request.getfixturevalue(fix_name)
        row = Row(content=content)
        assert row.training_category == training_cat

class TestTrain:
    def test_train_creation(self, row_exercises, row_routes):
        assert ClimbTrain(type=TrainingType.LEAD)
        assert ClimbTrain(type=TrainingType.BOULDER, rows=[row_routes])
        assert GymTrain(type=TrainingType.GPP)
        assert GymTrain(type=TrainingType.SFP, rows =[row_exercises])

    def test_add_row_err1(self, row_exercises):
        tr1 = ClimbTrain(type=TrainingType.LEAD)
        tr2 = ClimbTrain(type=TrainingType.BOULDER)
        with pytest.raises(TypeError):
            tr1.add_row(row_exercises)
            tr2.add_row(row_exercises)

    def test_add_row_err2(self, row_routes):
        tr1 = GymTrain(type=TrainingType.GPP)
        tr2 = GymTrain(type=TrainingType.SFP)
        with pytest.raises(TypeError):
            tr1.add_row(row_routes)
            tr2.add_row(row_routes)

    def test_add_row_ok(self, row_routes):
        t = ClimbTrain(type=TrainingType.LEAD)
        assert len(t.get_rows) == 0
        t.add_row(row_routes)
        assert len(t.get_rows) == 1


class TestWorkout:
    DATE = dt.datetime.now().date()

    def test_workout_creation(self, train_climb_empty):
        assert Workout(date=self.DATE)
        assert Workout(date=self.DATE, content=train_climb_empty)
        assert Workout(date=self.DATE, comments="one two three!")

    @pytest.mark.parametrize('comment', ["", "-"])
    def test_no_comments(self, comment):
        w = Workout(date=self.DATE, comments=comment)
        assert not len(w.comments)

    def test_date_err(self):
        with pytest.raises(exc.MissedDateError):
            Workout(123) # pyright: ignore

    def test_content(self, train_climb_fill):
        w = Workout(date=self.DATE, content=[train_climb_fill])
        assert len(w.get_content)

    def test_content2(self, train_climb_fill):
        w = Workout(date=self.DATE)
        assert len(w.get_content) == 0

        w.add_train(train_climb_fill)
        assert len(w.get_content) == 1


class TestJournal:
    def test_journal_creation(self, workout_climb, workout_gym):
        assert Journal() is not None
        assert Journal([workout_climb])
        assert Journal([workout_climb, workout_gym])

    @pytest.mark.parametrize('comment', ["", "-"])
    def test_no_comments(self, comment):
        j = Journal(comments=comment)
        assert len(j.comments) == 0

    def test_content(self, workout_climb, workout_gym):
        j = Journal()
        assert len(j) == 0
        j.add_workout(workout_climb)
        assert len(j) == 1
        j.add_workout(workout_gym)
        assert len(j) == 2

    def test_content_err(self):
        with pytest.raises(TypeError):
            Journal(content=[123])  # type: ignore

    def test_content_sort(self):
        w1 = Workout(date=dt.date(2026, 1, 1))
        w2 = Workout(date=dt.date(2026, 1, 2))
        w3 = Workout(date=dt.date(2026, 1, 3))
        j = Journal(content=[w3, w2])

        assert j.content[0].date < j.content[1].date
        j.add_workout(w1)
        assert j.content[0].date < j.content[1].date

    def test_period(self, workout_climb):
        j = Journal()
        assert j.period == (None, None)

        j.add_workout(workout_climb)
        assert j.period == (workout_climb.date, workout_climb.date)

    def test_add_workout_err(self):
        j = Journal()
        with pytest.raises(TypeError):
            j.add_workout(123) # type: ignore
