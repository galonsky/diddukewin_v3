from typing import Optional

from ddw.data.api_basketball.fetcher import APIBasketballFetcher
from ddw.data.api_basketball.models import APIBasketballGame
from ddw.evaluator import IEvaluator
from ddw.models import IGame


STATUSES_TO_IGNORE = {
    "NS",
    "POST",
    "CANC",
    "SUSP",
}


class APIBasketballEvaluator(IEvaluator):
    def __init__(self, fetcher: Optional[APIBasketballFetcher] = None):
        self.fetcher = fetcher or APIBasketballFetcher()

    def find_current_game(self) -> Optional[IGame]:
        all_games_response = self.fetcher.fetch_games()
        if not all_games_response["response"]:
            return None

        latest_game = max(
            (
                game
                for game in all_games_response["response"]
                if game["status"]["short"] not in STATUSES_TO_IGNORE
            ),
            key=lambda game: game["timestamp"],
            default=None,
        )
        if not latest_game:
            return None
        return APIBasketballGame.from_dict(latest_game)
