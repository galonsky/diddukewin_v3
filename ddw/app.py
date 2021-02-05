import requests

from ddw.config import should_tweet, get_config_value
from ddw.evaluator import Evaluator
from ddw.models import GameDisplay
from ddw.renderer import render
from ddw.twitter import post_tweet
from ddw.uploader import upload
import logging


if get_config_value("SENTRY_DSN"):
    import sentry_sdk
    from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration

    sentry_sdk.init(
        dsn=get_config_value("SENTRY_DSN"), integrations=[AwsLambdaIntegration()]
    )


logger = logging.getLogger()


def snitch():
    url = get_config_value("SNITCH_URL")
    if url:
        requests.get(url)


def run_update():
    game = Evaluator().find_current_game()
    logger.info(f"Found current game: {game}")
    game_display = GameDisplay(game)
    rendered = render(game_display)
    upload(rendered)

    if should_tweet() and game.has_ended():
        post_tweet(game_display.tweet_text)
    else:
        logger.info("Not tweeting since disabled or game not ended")

    snitch()


def lambda_handler(event, context):
    logger.setLevel(logging.INFO)

    run_update()
    return {"success": True}
