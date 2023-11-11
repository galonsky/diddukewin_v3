from unittest.mock import MagicMock

import pytest

from ddw.data.goduke.evaluator import GoDukeEvaluator
from ddw.data.goduke.models import GoDukeGame


@pytest.fixture
def goduke_schedule() -> str:
    with open("tests/test_data/goduke_schedule.txt", "r") as file:
        return file.read()


class TestFindCurrentGame:
    def test_finds_correct_score(self, goduke_schedule: str) -> None:
        fetcher = MagicMock()
        fetcher.fetch_schedule.return_value = goduke_schedule
        evaluator = GoDukeEvaluator(fetcher)
        assert evaluator.find_current_game() == GoDukeGame("L 73-78")
