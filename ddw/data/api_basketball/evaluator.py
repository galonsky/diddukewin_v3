from typing import Optional

from ddw.data.api_basketball.fetcher import APIBasketballFetcher
from ddw.evaluator import IEvaluator
from ddw.models import IGame


class APIBasketballEvaluator(IEvaluator):
    def __init__(self, fetcher: Optional[APIBasketballFetcher] = None):
        self.fetcher = fetcher or APIBasketballFetcher()

    def find_current_game(self) -> Optional[IGame]:
        all_games_response = self.fetcher.fetch_games()
        if not all_games_response["response"]:
            return None

        latest_game = max(
            all_games_response["response"], key=lambda game: game["timestamp"]
        )
