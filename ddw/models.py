import enum
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
import re
from typing import Dict, Optional

VALID_SCORE_PATTERN = re.compile(r"[0-9]+-[0-9]+")
LINK_PATTERN = re.compile(r"https?://")


class ResultType(enum.Enum):
    WIN = enum.auto()
    LOSS = enum.auto()
    NOT_YET = enum.auto()


class IGame(ABC):
    def has_ended(self) -> bool:
        return self.get_result_type() != ResultType.NOT_YET

    @abstractmethod
    def get_result_type(self) -> ResultType:
        ...

    @abstractmethod
    def get_score(self) -> str:
        ...


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

    RESULT_TO_WINLOSS = {
        ResultType.WIN: "W",
        ResultType.LOSS: "L",
        ResultType.NOT_YET: "",
    }

    def __init__(self, game: IGame):
        self.game = game

    @property
    def css_class(self):
        return self.RESULT_TO_CSS_CLASS[self.game.get_result_type()]

    @property
    def result_text(self):
        return self.RESULT_TO_TEXT[self.game.get_result_type()]

    @property
    def link_text(self):
        return f"{self.RESULT_TO_WINLOSS[self.game.get_result_type()]} {self.game.get_score()}"

    @property
    def tweet_text(self):
        return f"{self.result_text}. {self.game.get_score()} http://www.diddukewin.com"


class Tweet:
    DATETIME_FORMAT = "%a %b %d %X %z %Y"

    def __init__(self, text: str, created_at: Optional[datetime] = None):
        self.text = text
        self.created_at = created_at

    @classmethod
    def from_tweet_dict(cls, tweet_dict: Dict[str, str]):
        return cls(
            text=tweet_dict["text"],
            created_at=datetime.strptime(tweet_dict["created_at"], cls.DATETIME_FORMAT),
        )

    @property
    def text_without_link(self):
        link_match = LINK_PATTERN.search(self.text)
        if not link_match:
            return self.text.strip()
        return self.text[: link_match.start()].strip()


@dataclass
class Status:
    created_at: datetime
    content: str

    @classmethod
    def from_status_dict(cls, status_dict: dict) -> "Status":
        return cls(
            created_at=datetime.fromisoformat(
                status_dict["created_at"][0:-1] + "+00:00"
            ),
            content=re.sub("<[^<]+?>", "", status_dict["content"]),  # strip html
        )

    @property
    def text_without_link(self):
        link_match = LINK_PATTERN.search(self.content)
        if not link_match:
            return self.content.strip()
        return self.content[: link_match.start()].strip()

    @property
    def hours_ago(self) -> float:
        now = datetime.now(timezone.utc)
        return (now - self.created_at) / timedelta(hours=1)
