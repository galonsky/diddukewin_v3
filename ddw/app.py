import os
import requests

from ddw.config import should_tweet
from ddw.evaluator import Evaluator
from ddw.models import GameDisplay
from ddw.renderer import render
from ddw.twitter import post_tweet
from ddw.uploader import upload


def snitch():
    url = os.getenv("SNITCH_URL")
    if url:
        requests.get(url)


def run_update():
    game = Evaluator().find_current_game()
    game_display = GameDisplay(game)
    rendered = render(game_display)
    upload(rendered)

    if should_tweet() and game.has_ended():
        post_tweet(game_display.tweet_text)

    snitch()
