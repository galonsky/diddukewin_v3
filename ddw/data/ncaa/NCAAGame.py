from dataclasses import dataclass

from ddw.models import IGame, ResultType


@dataclass
class NCAAGame(IGame):
    result_type: ResultType
    score: str

    def get_result_type(self) -> ResultType:
        return self.result_type

    def get_score(self) -> str:
        return self.score
