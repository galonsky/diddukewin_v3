from unittest.mock import MagicMock

import pytest

from ddw.data.espn.evaluator import ESPNEvaluator
from ddw.exceptions import NoGamesFoundException
from ddw.data.espn.models import ESPNGame


class TestFindCurrentGame:
    @pytest.fixture
    def mock_fetcher(self):
        return MagicMock()

    @pytest.fixture
    def mock_parser(self):
        parser = MagicMock()

        def factory(games):
            parser.parse.return_value = games
            return parser

        return factory

    def test_no_games_raises(self, mock_fetcher, mock_parser):
        evaluator = ESPNEvaluator(mock_fetcher, mock_parser([]))
        with pytest.raises(NoGamesFoundException):
            evaluator.find_current_game()

    def test_one_game_returns_single_game(self, mock_fetcher, mock_parser):
        game = ESPNGame(
            date="foo", opponent="bar", winlose="L", score="99-1", urlslug="bar"
        )
        evaluator = ESPNEvaluator(mock_fetcher, mock_parser([game]))
        assert evaluator.find_current_game() == game

    def test_two_games_second_has_valid_returns_second(self, mock_fetcher, mock_parser):
        game1 = ESPNGame(
            date="foo", opponent="bar", winlose="L", score="99-1", urlslug="bar"
        )
        game2 = ESPNGame(
            date="foo", opponent="bar", winlose="L", score="98-1", urlslug="bar"
        )

        evaluator = ESPNEvaluator(mock_fetcher, mock_parser([game1, game2]))
        assert evaluator.find_current_game() == game2

    def test_two_games_second_no_valid_returns_first(self, mock_fetcher, mock_parser):
        game1 = ESPNGame(
            date="foo", opponent="bar", winlose="L", score="99-1", urlslug="bar"
        )
        game2 = ESPNGame(
            date="foo", opponent="bar", winlose="L", score="7:00 PM", urlslug="bar"
        )

        evaluator = ESPNEvaluator(mock_fetcher, mock_parser([game1, game2]))
        assert evaluator.find_current_game() == game1
