from dataclasses import dataclass

from ddw.models import IGame, ResultType


@dataclass
class GoDukeGame(IGame):
    score_str: str

    def has_ended(self) -> bool:
        return True  # does not support live scores

    def get_result_type(self) -> ResultType:
        return ResultType.WIN if self.score_str.startswith("W") else ResultType.LOSS

    def get_score(self) -> str:
        return self.score_str[2:]
