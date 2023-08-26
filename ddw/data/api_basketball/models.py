from dataclasses import dataclass

from ddw.data.api_basketball.constants import TEAM_ID
from ddw.models import IGame, ResultType


FINISHED_STATUSES = {
    "FT",
    "AOT",
}


@dataclass
class APIBasketballGame(IGame):
    status: str
    duke_score: int
    other_score: int

    @classmethod
    def from_dict(cls, game_dict: dict) -> "APIBasketballGame":
        home_team_id = game_dict["teams"]["home"]["id"]
        duke_home = home_team_id == TEAM_ID
        return cls(
            status=game_dict["status"]["short"],
            duke_score=game_dict["scores"]["home"]["total"]
            if duke_home
            else game_dict["scores"]["away"]["total"],
            other_score=game_dict["scores"]["away"]["total"]
            if duke_home
            else game_dict["scores"]["home"]["total"],
        )

    def get_result_type(self) -> ResultType:
        ended = self.status in FINISHED_STATUSES
        if not ended:
            return ResultType.NOT_YET

        return ResultType.WIN if self.duke_score > self.other_score else ResultType.LOSS

    def get_score(self) -> str:
        return f"{self.duke_score}-{self.other_score}"
