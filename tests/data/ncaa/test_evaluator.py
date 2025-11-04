import json
from datetime import datetime
from unittest.mock import MagicMock
from zoneinfo import ZoneInfo

import pytest

from ddw.data.ncaa.NCAAGame import NCAAGame
from ddw.data.ncaa.evaluator import NCAAEvaluator
from ddw.models import ResultType


@pytest.fixture
def ncaa_new() -> str:
    with open("tests/test_data/ncaa_new.json", "r") as file:
        return json.loads(file.read())


class TestFindCurrentGame:
    def test_when_no_scoreboard_returns_none(self, ncaa_new: str) -> None:
        fetcher = MagicMock()
        fetcher.fetch_scoreboard.return_value = None
        evaluator = NCAAEvaluator(fetcher)
        assert evaluator.find_current_game() is None

    def test_when_pregame_returns_none(self, ncaa_new: str) -> None:
        fetcher = MagicMock()
        fetcher.fetch_scoreboard.return_value = ncaa_new
        evaluator = NCAAEvaluator(fetcher, team_short_name="Georgetown")
        assert evaluator.find_current_game() is None

    def test_final_winner(self, ncaa_new: str) -> None:
        fetcher = MagicMock()
        fetcher.fetch_scoreboard.return_value = ncaa_new
        evaluator = NCAAEvaluator(fetcher, team_short_name="Drake")
        assert evaluator.find_current_game() == NCAAGame(ResultType.WIN, "77-71")

    def test_final_loser(self, ncaa_new: str) -> None:
        fetcher = MagicMock()
        fetcher.fetch_scoreboard.return_value = ncaa_new
        evaluator = NCAAEvaluator(fetcher, team_short_name="Northern Ariz.")
        assert evaluator.find_current_game() == NCAAGame(ResultType.LOSS, "71-77")

    def test_in_progress(self, ncaa_new: str) -> None:
        fetcher = MagicMock()
        fetcher.fetch_scoreboard.return_value = ncaa_new
        evaluator = NCAAEvaluator(fetcher, team_short_name="Buffalo")
        assert evaluator.find_current_game() == NCAAGame(ResultType.NOT_YET, "76-73")

    def test_when_before_6_subtracts_a_day(self, ncaa_new: str) -> None:
        fetcher = MagicMock()
        fetcher.fetch_scoreboard.return_value = ncaa_new
        clock = MagicMock()
        clock.now.return_value = datetime(
            2025, 3, 15, 1, tzinfo=ZoneInfo("America/New_York")
        )
        evaluator = NCAAEvaluator(fetcher, clock)
        evaluator.find_current_game()
        fetcher.fetch_scoreboard.assert_called_once_with(
            datetime(2025, 3, 14, 1, tzinfo=ZoneInfo("America/New_York"))
        )

    def test_when_after_6_subtracts_uses_real_time(self, ncaa_new: str) -> None:
        fetcher = MagicMock()
        fetcher.fetch_scoreboard.return_value = ncaa_new
        clock = MagicMock()
        clock.now.return_value = datetime(
            2025, 3, 14, 23, tzinfo=ZoneInfo("America/New_York")
        )
        evaluator = NCAAEvaluator(fetcher, clock)
        evaluator.find_current_game()
        fetcher.fetch_scoreboard.assert_called_once_with(
            datetime(2025, 3, 14, 23, tzinfo=ZoneInfo("America/New_York"))
        )
