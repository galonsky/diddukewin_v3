from dataclasses import dataclass

from ddw.models import IGame, VALID_SCORE_PATTERN, ResultType


@dataclass
class ESPNGame(IGame):
    date: str
    opponent: str
    winlose: str
    score: str
    urlslug: str

    def has_valid_score(self) -> bool:
        return bool(VALID_SCORE_PATTERN.search(self.score))

    def get_link(self) -> str:
        if self.has_ended():
            return "http://espn.go.com/ncb/recap{}".format(self.urlslug)
        else:
            return "http://espn.go.com/ncb/gamecast{}".format(self.urlslug)

    def get_result_type(self) -> ResultType:
        if self.winlose == "L":
            return ResultType.LOSS
        elif self.winlose == "W":
            return ResultType.WIN
        else:
            return ResultType.NOT_YET

    def get_score(self) -> str:
        return self.score
