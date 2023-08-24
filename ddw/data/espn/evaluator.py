import logging

from ddw.evaluator import IEvaluator
from ddw.exceptions import NoGamesFoundException
from ddw.data.espn.fetcher import ScoreFetcher
from ddw.data.espn.models import ESPNGame
from ddw.data.espn.parser import Parser


logger = logging.getLogger()


class ESPNEvaluator(IEvaluator):
    def __init__(
        self, fetcher: ScoreFetcher = ScoreFetcher(), parser: Parser = Parser()
    ):
        self.fetcher = fetcher
        self.parser = parser

    def find_current_game(self) -> ESPNGame:
        body = self.fetcher.fetch()
        logger.info("Fetched content")
        games = list(self.parser.parse(body))
        if not games:
            raise NoGamesFoundException()
        if len(games) < 2:
            return games[0]

        if games[1].has_valid_score():
            return games[1]
        else:
            return games[0]
