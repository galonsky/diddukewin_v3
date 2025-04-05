from datetime import datetime, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

from ddw.clock import Clock
from ddw.data.ncaa.NCAAGame import NCAAGame
from ddw.data.ncaa.fetcher import NCAAFetcher
from ddw.evaluator import IEvaluator
from ddw.models import IGame, ResultType


class NCAAEvaluator(IEvaluator):
    def __init__(
        self, fetcher: Optional[NCAAFetcher] = None, clock: Optional[Clock] = None
    ) -> None:
        self.fetcher = fetcher or NCAAFetcher()
        self.clock = clock or Clock()

    def find_current_game(self) -> Optional[IGame]:
        now = self.clock.now()
        if now.hour < 6:
            now = now - timedelta(days=1)
        scoreboard = self.fetcher.fetch_scoreboard(now)
        if not scoreboard:
            return None
        possible_games = [
            game["game"]
            for game in scoreboard["games"]
            if game["game"]["home"]["names"]["short"] == "Duke"
            or game["game"]["away"]["names"]["short"] == "Duke"
        ]
        if not possible_games:
            return None
        if len(possible_games) > 1:
            raise Exception("more than one game?")

        game = possible_games[0]
        if game["gameState"] == "pre":
            return None

        if game["home"]["names"]["short"] == "Duke":
            duke_info = game["home"]
            away_info = game["away"]
        else:
            duke_info = game["away"]
            away_info = game["home"]

        score_str = f"{duke_info['score']}-{away_info['score']}"
        result_type = self._get_result_type(game, duke_info)
        return NCAAGame(result_type, score_str)

    @staticmethod
    def _get_result_type(game: dict, duke_info: dict) -> ResultType:
        if game["gameState"] != "final":
            return ResultType.NOT_YET

        return ResultType.WIN if duke_info["winner"] else ResultType.LOSS
