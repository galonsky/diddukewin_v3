from dataclasses import dataclass

@dataclass
class Game:
    date: str
    opponent: str
    winlose: str
    score: str
    urlslug: str
