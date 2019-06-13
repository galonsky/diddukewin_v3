from ddw.exceptions import NoGamesFoundException
from ddw.fetcher import ScoreFetcher
from ddw.models import Game
from ddw.parser import Parser


class Evaluator:
    def __init__(
        self, fetcher: ScoreFetcher = ScoreFetcher(), parser: Parser = Parser()
    ):
        self.fetcher = fetcher
        self.parser = parser

    def find_current_game(self) -> Game:
        body = self.fetcher.fetch()
        games = list(self.parser.parse(body))
        if not games:
            raise NoGamesFoundException()
        if len(games) < 2:
            return games[0]

        if games[1].has_valid_score():
            return games[1]
        else:
            return games[0]
