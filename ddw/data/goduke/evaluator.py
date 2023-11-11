import re
from typing import Optional

from ddw.data.goduke.fetcher import GoDukeFetcher
from ddw.data.goduke.models import GoDukeGame
from ddw.evaluator import IEvaluator
from ddw.models import IGame


WIN_LOSS_PATTERN = re.compile(r"[WL] \d+-\d+")


class GoDukeEvaluator(IEvaluator):
    def __init__(self, fetcher: Optional[GoDukeFetcher] = None) -> None:
        self.fetcher = fetcher or GoDukeFetcher()

    def find_current_game(self) -> Optional[IGame]:
        schedule = self.fetcher.fetch_schedule()
        all_matches = WIN_LOSS_PATTERN.findall(schedule)
        if not all_matches:
            return None

        latest = all_matches[-1]
        return GoDukeGame(latest)
