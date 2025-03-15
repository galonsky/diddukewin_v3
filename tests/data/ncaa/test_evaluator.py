import json
from datetime import datetime
from unittest.mock import MagicMock
from zoneinfo import ZoneInfo

import pytest

from ddw.data.ncaa.NCAAGame import NCAAGame
from ddw.data.ncaa.evaluator import NCAAEvaluator
from ddw.models import ResultType


@pytest.fixture
def ncaa_win() -> str:
    with open("tests/test_data/ncaa_win.json", "r") as file:
        return json.loads(file.read())


@pytest.fixture
def ncaa_loss() -> str:
    with open("tests/test_data/ncaa_loss.json", "r") as file:
        return json.loads(file.read())


@pytest.fixture
def ncaa_no_game() -> str:
    with open("tests/test_data/ncaa_no_game.json", "r") as file:
        return json.loads(file.read())


@pytest.fixture
def ncaa_in_progress() -> str:
    with open("tests/test_data/ncaa_in_progress.json", "r") as file:
        return json.loads(file.read())


@pytest.fixture
def ncaa_pregame() -> str:
    with open("tests/test_data/ncaa_pregame.json", "r") as file:
        return json.loads(file.read())


class TestFindCurrentGame:
    def test_finds_win(self, ncaa_win: str) -> None:
        fetcher = MagicMock()
        fetcher.fetch_scoreboard.return_value = ncaa_win
        evaluator = NCAAEvaluator(fetcher)
        assert evaluator.find_current_game() == NCAAGame(ResultType.WIN, "74-71")

    def test_finds_loss(self, ncaa_loss: str) -> None:
        fetcher = MagicMock()
        fetcher.fetch_scoreboard.return_value = ncaa_loss
        evaluator = NCAAEvaluator(fetcher)
        assert evaluator.find_current_game() == NCAAGame(ResultType.LOSS, "71-77")

    def test_finds_no_game(self, ncaa_no_game: str) -> None:
        fetcher = MagicMock()
        fetcher.fetch_scoreboard.return_value = ncaa_no_game
        evaluator = NCAAEvaluator(fetcher)
        assert evaluator.find_current_game() is None

    def test_finds_in_progress(self, ncaa_in_progress: str) -> None:
        fetcher = MagicMock()
        fetcher.fetch_scoreboard.return_value = ncaa_in_progress
        evaluator = NCAAEvaluator(fetcher)
        assert evaluator.find_current_game() == NCAAGame(ResultType.NOT_YET, "50-45")

    def test_returns_none_if_pregame(self, ncaa_pregame: str) -> None:
        fetcher = MagicMock()
        fetcher.fetch_scoreboard.return_value = ncaa_pregame
        evaluator = NCAAEvaluator(fetcher)
        assert evaluator.find_current_game() is None

    def test_when_before_6_subtracts_a_day(self, ncaa_win: str) -> None:
        fetcher = MagicMock()
        fetcher.fetch_scoreboard.return_value = ncaa_win
        clock = MagicMock()
        clock.now.return_value = datetime(
            2025, 3, 15, 1, tzinfo=ZoneInfo("America/New_York")
        )
        evaluator = NCAAEvaluator(fetcher, clock)
        evaluator.find_current_game()
        fetcher.fetch_scoreboard.assert_called_once_with(
            datetime(2025, 3, 14, 1, tzinfo=ZoneInfo("America/New_York"))
        )

    def test_when_after_6_subtracts_uses_real_time(self, ncaa_win: str) -> None:
        fetcher = MagicMock()
        fetcher.fetch_scoreboard.return_value = ncaa_win
        clock = MagicMock()
        clock.now.return_value = datetime(
            2025, 3, 14, 23, tzinfo=ZoneInfo("America/New_York")
        )
        evaluator = NCAAEvaluator(fetcher, clock)
        evaluator.find_current_game()
        fetcher.fetch_scoreboard.assert_called_once_with(
            datetime(2025, 3, 14, 23, tzinfo=ZoneInfo("America/New_York"))
        )
