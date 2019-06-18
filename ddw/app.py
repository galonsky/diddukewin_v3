from ddw.evaluator import Evaluator
from ddw.models import GameDisplay
from ddw.renderer import render
from ddw.uploader import upload


def run_update():
    game = Evaluator().find_current_game()
    rendered = render(GameDisplay(game))
    upload(rendered)
