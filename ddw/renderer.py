from jinja2 import Environment, PackageLoader, select_autoescape

from ddw.models import GameDisplay

env = Environment(
    loader=PackageLoader("ddw", "templates"), autoescape=select_autoescape(["html"])
)


def render(game_display: GameDisplay) -> str:
    template = env.get_template("index.html")
    return template.render(game_display=game_display)
