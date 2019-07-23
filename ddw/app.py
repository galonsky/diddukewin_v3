import os

from ddw.evaluator import Evaluator
from ddw.models import GameDisplay
from ddw.renderer import render
from ddw.twitter import post_tweet
from ddw.uploader import upload


TWEETING_ENABLED = bool(os.getenv("TWEETING_ENABLED"))


def run_update():
    # todo tests
    game = Evaluator().find_current_game()
    game_display = GameDisplay(game)
    rendered = render(game_display)
    upload(rendered)

    if TWEETING_ENABLED and game.has_ended():
        post_tweet(game_display.tweet_text)
