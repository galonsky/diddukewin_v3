import enum
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
import re
from typing import Dict, Optional

VALID_SCORE_PATTERN = re.compile(r"[0-9]+-[0-9]+")
ENDED_PATTERN = re.compile(r"[WL]")
LINK_PATTERN = re.compile(r"https?://")


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

    @property
    def tweet_text(self):
        return f"{self.result_text}. {self.game.score} http://www.diddukewin.com"


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
