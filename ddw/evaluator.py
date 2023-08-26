from abc import ABC, abstractmethod
from typing import Optional

from ddw.models import IGame


class IEvaluator(ABC):
    @abstractmethod
    def find_current_game(self) -> Optional[IGame]:
        ...
