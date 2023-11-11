import pytest

from ddw.data.espn.models import ESPNGame
from ddw.data.espn.parser import Parser


class TestParse:
    @pytest.fixture
    def file_with_two_games(self):
        with open("tests/test_data/score_simplified.html", "r") as file:
            return file.read()

    @pytest.fixture
    def mets(self):
        with open("tests/test_data/mets.html", "r") as file:
            return file.read()

    @pytest.fixture
    def cubs(self):
        with open("tests/test_data/cubs.html", "r") as file:
            return file.read()

    @pytest.fixture
    def file_with_one_complete_game(self):
        with open("tests/test_data/score.html", "r") as file:
            return file.read()

    def test_one_game_gets_correct_fields(self, file_with_one_complete_game):
        games = list(Parser().parse(file_with_one_complete_game))
        assert games == [
            ESPNGame(
                date="Sun, 3/31",
                opponent="MSU",
                winlose="L",
                urlslug="?gameId=401123387&version=mobile&teamId=150",
                score="67-68",
            )
        ]

    def test_two_games(self, file_with_two_games):
        games = list(Parser().parse(file_with_two_games))
        assert games == [
            ESPNGame(
                date="Sun, 3/32",
                opponent="LSU",
                winlose="",
                urlslug="?gameId=401123387&version=mobile&teamId=150",
                score="",
            ),
            ESPNGame(
                date="Sun, 3/31",
                opponent="MSU",
                winlose="L",
                urlslug="?gameId=401123387&version=mobile&teamId=150",
                score="67-68",
            ),
        ]

    def test_mets(self, mets):
        games = list(Parser().parse(mets))
        assert games == [
            ESPNGame(
                date="Sat, 6/8",
                opponent="COL",
                winlose="W",
                urlslug="?gameId=401075687&version=mobile&teamId=21",
                score="5-3",
            ),
            ESPNGame(
                date="Sun, 6/9",
                opponent="COL",
                winlose="W",
                urlslug="?gameId=401075702&version=mobile&teamId=21",
                score="6-1",
            ),
            ESPNGame(
                date="Mon, 6/10",
                opponent="@NYY",
                winlose="7:05 PM",
                urlslug="?gameId=401075715&version=mobile&teamId=21",
                score="",
            ),
            ESPNGame(
                date="Tue, 6/11",
                opponent="@NYY",
                winlose="7:00 PM",
                urlslug="?gameId=401075727&version=mobile&teamId=21",
                score="",
            ),
        ]

    def test_cubs(self, cubs):
        games = list(Parser().parse(cubs))
        assert games == [
            ESPNGame(
                date="Sat, 6/8",
                opponent="STL",
                winlose="W",
                urlslug="?gameId=401075694&version=mobile&teamId=16",
                score="9-4",
            ),
            ESPNGame(
                date="Sun, 6/9",
                opponent="STL",
                winlose="TOP 5TH",
                urlslug="?gameId=401075709&version=mobile&teamId=16",
                score="1-1",
            ),
            ESPNGame(
                date="Mon, 6/10",
                opponent="@COL",
                winlose="8:40 PM",
                urlslug="?gameId=401075722&version=mobile&teamId=16",
                score="",
            ),
            ESPNGame(
                date="Tue, 6/11",
                opponent="@COL",
                winlose="8:40 PM",
                urlslug="?gameId=401075737&version=mobile&teamId=16",
                score="",
            ),
        ]
