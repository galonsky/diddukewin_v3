import re
from typing import Iterator

from ddw.models import Game

INITIAL_PATTERN = re.compile(r"teamschedule")
DATA_PATTERN = re.compile(r"gamecast(?P<urlslug>[^']*)'>(?P<datum>[^<]*)<")

DATA_GROUPS = ("date", "opponent", "winlose", "score")


class Parser:
    def parse(self, body) -> Iterator[Game]:
        match = INITIAL_PATTERN.search(body)
        if not match:
            raise ValueError("cannot find team schedule")
        start = match.start()
        matches = DATA_PATTERN.finditer(body, pos=start)
        while True:
            game_dict = {}
            for group_name in DATA_GROUPS:
                try:
                    match = next(matches)
                except StopIteration:
                    return

                game_dict["urlslug"] = match.group("urlslug").strip()
                game_dict[group_name] = match.group("datum").strip()
            yield Game(**game_dict)
