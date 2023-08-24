from abc import ABC, abstractmethod
from ddw.models import IGame


class IEvaluator(ABC):
    @abstractmethod
    def find_current_game(self) -> IGame:
        ...
