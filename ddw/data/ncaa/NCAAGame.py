from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from ddw.models import IGame, ResultType


@dataclass
class NCAAGame(IGame):
    result_type: ResultType
    score: str
    # Live-game details; excluded from equality so they never affect result checks.
    game_state: str = field(default="", compare=False)
    start_time: Optional[datetime] = field(default=None, compare=False)
    period: str = field(default="", compare=False)
    clock: str = field(default="", compare=False)

    def get_result_type(self) -> ResultType:
        return self.result_type

    def get_score(self) -> str:
        return self.score

    def is_pregame(self) -> bool:
        return self.game_state == "P"

    def get_start_time(self) -> Optional[datetime]:
        return self.start_time
