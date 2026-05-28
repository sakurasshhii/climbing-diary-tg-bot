import pytest
from app.services.parser import JournalParser


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
