import datetime as dt

import pytest

import app.domain.exceptions as exc
from app.domain.enums import TrainingCategory, TrainingType
from app.domain.models import (ClimbTrain, Exercise, GymTrain, Journal, Route,
                               Row, Workout)


class TestExercise:
    def test_exercise_creation(self):
        assert Exercise(name='Ex 1', repeats=(1, 2, 3))

    def test__name_err(self):
        with pytest.raises(ValueError):
            Exercise(name='', repeats=(1, 2, 3))

    def test__repeats_err(self):
        with pytest.raises(ValueError):
            Exercise(name='Ex 1', repeats=(-1, 1, 1))

    @pytest.mark.parametrize(
        "name,repeats,out",
        [
            ("pull-ups", (1,), "pull-ups 1"),
            ("squads", (1, 2, 3), "squads 1/2/3")
        ]
    )
    def test_str(self, name, repeats, out):
        ex = Exercise(name=name, repeats=repeats)
        assert str(ex) == out


class TestRoute:
    def test_route_creation(self):
        assert Route(grade='6a', falls_no=0, flash=False)

    @pytest.mark.parametrize(
        'grade',
        ['6d', '6', '10a']
    )
    def test_grade_err(self, grade):
        with pytest.raises(ValueError):
            Route(grade=grade, falls_no=0, flash=False)

    def test_falls_err(self):
        with pytest.raises(ValueError):
            Route(grade='6a', falls_no=-1, flash=False)

    def test_flash_err(self):
        with pytest.raises(ValueError):
            Route(grade='6a', falls_no=1, flash=True)

    @pytest.mark.parametrize(
        "grade,falls,flash,red_point,out",
        [
            ("6a", False, False, False, "6a"),
            ("6a+", False, False, False, "6a+"),
            ("6a+", True, False, False, "6a+:"),
            ("6a", 1, False, False, "6a:1"),
            ("6a", False, True, False, "6a f"),
            ("6a", False, False, True, "6a rp"),
        ]
    )
    def test_str(self, grade, falls, flash, red_point, out):
        route = Route(
            grade=grade,
            falls_no=falls,
            flash=flash,
            red_point=red_point,
        )
        assert str(route) == out


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

    @pytest.mark.parametrize(
        "content,comments,out",
        [
            ([Route(grade="6a")], "-", "6a"),
            ([Route(grade="6a"), Route(grade="6a")], "-", "6a, 6a"),
            ([Route(grade="6a"), Route(grade="6a")], "my comment", "6a, 6a — my comment"),
            ([Exercise(name="ex 1", repeats=(100,))], "-", "ex 1 100"),
            ([Exercise(name="ex 1", repeats=(1, 2, 3))], "-", "ex 1 1/2/3"),
            ([Exercise(name="ex 1", repeats=(1, 2, 3))], "my comment", "ex 1 1/2/3 — my comment"),
        ]
    )
    def test_str(self, content, comments, out):
        row = Row(content=content, comments=comments)
        assert str(row) == out

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

    @pytest.mark.parametrize(
        "tr_type,rows,comments,out",
        [
            (TrainingType.LEAD, [Row([Route(grade="6a")])], "-", "Трудность\n6a"),
            (TrainingType.BOULDER, [Row([Route(grade="6a")])], "abc", "Боулдер\n6a\nКомментарии: abc"),
            (TrainingType.GPP, [Row([Exercise("ex", repeats=(1, 2, 3))])], "-", "ОФП\nex 1/2/3"),
            (TrainingType.SFP, [Row([Exercise("ex", repeats=(1,))])], "abc", "СФП\nex 1\nКомментарии: abc"),
        ]
    )
    def test_str(self, tr_type, rows, comments, out):
        t = ClimbTrain(type=tr_type, rows=rows, comments=comments)
        assert str(t) == out


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

    @pytest.mark.parametrize(
        "date,content,comments,out",
        [
            (dt.date(2026, 5, 5), [], "-", "05.05.2026"),
            (dt.date(2026, 5, 5), [ClimbTrain(TrainingType.LEAD)], "-", "05.05.2026\nТрудность"),
            (
                dt.date(2026, 5, 5),
                [ClimbTrain(TrainingType.BOULDER, [Row([Route("6a")]), Row([Route("6a")])])],
                "abc",
                "05.05.2026\nБоулдер\n6a\n6a\nКомментарии: abc"
            )
        ]
    )
    def test_str(self, date, content, comments, out):
        w = Workout(date=date, content=content, comments=comments)
        assert str(w) == out


class TestJournal:
    def test_journal_creation(self, workout_climb, workout_gym):
        assert Journal() is not None
        assert Journal(content=[workout_climb]).content == [workout_climb]

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

    @pytest.mark.parametrize(
        "content,comments,out",
        [
            ([], "-", "Дневник ...-...\n \nНет тренировок."),
            (
                [
                    Workout(date=dt.date(2026, 5, 1), content=[ClimbTrain(TrainingType.LEAD)]),
                    Workout(date=dt.date(2026, 5, 5), content=[ClimbTrain(TrainingType.BOULDER)]),
                ],
                "my comments",
                "Дневник 01.05.2026-05.05.2026\nКомментарии: my comments\n \n01.05.2026\nТрудность\n——————————\n05.05.2026\nБоулдер"
            )
        ]
    )
    def test_str(self, content, comments, out):
        j = Journal(content=content, comments=comments)
        assert str(j) == out
