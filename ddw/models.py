import enum
from dataclasses import dataclass
import re

VALID_SCORE_PATTERN = re.compile(r"[0-9]+-[0-9]+")
ENDED_PATTERN = re.compile(r"[WL]")


class ResultType(enum.Enum):
    WIN = enum.auto()
    LOSS = enum.auto()
    NOT_YET = enum.auto()


@dataclass
class Game:
    date: str
    opponent: str
    winlose: str
    score: str
    urlslug: str

    def has_valid_score(self) -> bool:
        return bool(VALID_SCORE_PATTERN.search(self.score))

    def has_ended(self):
        return bool(ENDED_PATTERN.search(self.winlose))

    def get_link(self):
        if self.has_ended():
            return "http://espn.go.com/ncb/recap{}".format(self.urlslug)
        else:
            return "http://espn.go.com/ncb/gamecast{}".format(self.urlslug)

    def get_result_type(self):
        if self.winlose == "L":
            return ResultType.LOSS
        elif self.winlose == "W":
            return ResultType.WIN
        else:
            return ResultType.NOT_YET


class GameDisplay:

    RESULT_TO_CSS_CLASS = {
        ResultType.WIN: "yes",
        ResultType.LOSS: "no",
        ResultType.NOT_YET: "notyet",
    }

    RESULT_TO_TEXT = {
        ResultType.WIN: "YES",
        ResultType.LOSS: "NO",
        ResultType.NOT_YET: "NOT YET",
    }

    def __init__(self, game: Game):
        self.game = game

    @property
    def link(self):
        return self.game.get_link()

    @property
    def css_class(self):
        return self.RESULT_TO_CSS_CLASS[self.game.get_result_type()]

    @property
    def result_text(self):
        return self.RESULT_TO_TEXT[self.game.get_result_type()]

    @property
    def link_text(self):
        return f"{self.game.winlose} {self.game.score}"
