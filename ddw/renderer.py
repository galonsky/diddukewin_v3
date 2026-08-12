import json
import re
from typing import Optional

from minify_html import minify
from jinja2 import Environment, PackageLoader, select_autoescape

from ddw.models import GameDisplay, IGame, LastKnownGame, ResultType

env = Environment(
    loader=PackageLoader("ddw", "templates"), autoescape=select_autoescape(["html"])
)


def render(game_display: GameDisplay) -> str:
    template = env.get_template("index.html")
    rendered = minify(template.render(game_display=game_display), keep_comments=True)
    state = json.dumps(
        {
            "result": game_display.game.get_result_type().name,
            "score": game_display.game.get_score(),
        },
        separators=(",", ":"),
    )
    return f"{rendered}<!--ddw-state:{state}-->"


def parse_last_known_game(content: str) -> Optional[IGame]:
    state_match = re.search(r"<!--\s*ddw-state:\s*(\{.*?\})\s*-->", content)
    if state_match:
        try:
            state = json.loads(state_match.group(1))
            return LastKnownGame(ResultType[state["result"]], state["score"])
        except KeyError, TypeError, ValueError:
            pass

    result_match = re.search(
        r'class\s*=\s*["\']?(?P<result>yes|no|notyet)\b', content, re.IGNORECASE
    )
    score_match = re.search(
        r"\b(?:[WL]\s+)?(?P<score>\d+-\d+)\b", content, re.IGNORECASE
    )
    if not result_match or not score_match:
        return None

    result_by_css_class = {
        css_class: result_type
        for result_type, css_class in GameDisplay.RESULT_TO_CSS_CLASS.items()
    }
    result_type = result_by_css_class[result_match.group("result").lower()]
    return LastKnownGame(result_type, score_match.group("score"))
