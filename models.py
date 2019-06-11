from dataclasses import dataclass
import re

VALID_SCORE_PATTERN = re.compile(r'[0-9]+-[0-9]+')
ENDED_PATTERN = re.compile(r'[WL]')

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
            return 'http://espn.go.com/ncb/recap{}'.format(self.urlslug)
        else:
            return 'http://espn.go.com/ncb/gamecast{}'.format(self.urlslug)
