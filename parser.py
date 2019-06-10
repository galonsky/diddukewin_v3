import re
from typing import Iterator

from models import Game

INITIAL_PATTERN = re.compile(r'teamschedule')
DATA_PATTERN = re.compile(
    r"gamecast(?P<urlslug>[^']*)'>(?P<datum>[^<]*)<"
)

DATA_GROUPS = (
    'date',
    'opponent',
    'winlose',
    'score',
)

class Parser:
    def __init__(self, body):
        self.body = body

    def parse(self) -> Iterator[Game]:
        match = INITIAL_PATTERN.search(self.body)
        start = match.start()
        matches = DATA_PATTERN.finditer(self.body, pos=start)
        while True:
            game_dict = {}
            for group_name in DATA_GROUPS:
                try:
                    match = next(matches)
                except StopIteration:
                    return

                game_dict['urlslug'] = match.group('urlslug').strip()
                game_dict[group_name] = match.group('datum').strip()
            yield Game(**game_dict)
