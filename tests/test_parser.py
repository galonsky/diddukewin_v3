import pytest

from models import Game
from parser import Parser


class TestParse:
    @pytest.fixture
    def file_with_two_games(self):
        with open('score_simplified.html', 'r') as file:
            return file.read()

    @pytest.fixture
    def mets(self):
        with open('mets.html', 'r') as file:
            return file.read()

    @pytest.fixture
    def cubs(self):
        with open('cubs.html', 'r') as file:
            return file.read()

    @pytest.fixture
    def file_with_one_complete_game(self):
        with open('score.html', 'r') as file:
            return file.read()

    def test_one_game_gets_correct_fields(self, file_with_one_complete_game):
        games = list(Parser(file_with_one_complete_game).parse())
        assert games == [
            Game(
                date='Sun, 3/31',
                opponent='MSU',
                winlose='L',
                urlslug='?gameId=401123387&version=mobile&teamId=150',
                score='67-68',
            )
        ]

    def test_two_games(self, file_with_two_games):
        games = list(Parser(file_with_two_games).parse())
        assert games == [
            Game(
                date='Sun, 3/32',
                opponent='LSU',
                winlose='',
                urlslug='?gameId=401123387&version=mobile&teamId=150',
                score='',
            ),
            Game(
                date='Sun, 3/31',
                opponent='MSU',
                winlose='L',
                urlslug='?gameId=401123387&version=mobile&teamId=150',
                score='67-68',
            ),
        ]

    def test_mets(self, cubs):
        games = list(Parser(cubs).parse())
        assert games is not None
