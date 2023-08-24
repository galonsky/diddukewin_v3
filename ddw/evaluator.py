from abc import ABC, abstractmethod

from ddw.models import Game


class IEvaluator(ABC):
    @abstractmethod
    def find_current_game(self) -> Game:
        ...
