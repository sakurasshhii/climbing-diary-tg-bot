import pytest
from app.services.parser import JournalParser
from app.domain.enums import TrainingCategory
from app.domain.models import Row, Route, Exercise


class TestParser:
    @pytest.mark.parametrize(
        "route",
        "6a, 6a+, 6a:1, 6a:5, 6a:, 6a f, 6a rp, 6a+ f, 6a+ rp, 6a:10".split(", ")
    )
    def test_get_route_ok(self, route):
        assert JournalParser.get_route(route)

    @pytest.mark.parametrize(
        "route",
        "6d, 3a, 10b, 6a+: f, 6a f rp, 6a: rp, 6a: f rp, 6a d, 6a:100".split(", ")
    )
    def test_get_route_invalid(self, route):
        with pytest.raises(ValueError):
            JournalParser.get_route(route)

    def test_parse_rows(self):
        rows = JournalParser.parse_rows(
            text="""6a, 6a+ - first
            6b:, 6b f - second
            6c rp""",
            training_category=TrainingCategory.CLIMBING,
        )
        assert rows == [
            Row([Route("6a"), Route("6a+")], "first"),
            Row([Route("6b", falls= True), Route("6b", flash=True)], "second"),
            Row([Route("6c", red_point=True)])
        ]
