import os

from ddw.mastodon import tooter
from ddw.twitter import tweeter


if os.getenv("XRAY_ENABLED"):
    from aws_xray_sdk.core import patch_all

    patch_all()


from ddw.config import should_tweet, ssm_config, should_toot
from ddw.data.espn.evaluator import ESPNEvaluator
from ddw.models import GameDisplay
from ddw.renderer import render
from ddw.uploader import upload
import logging


if os.getenv("SENTRY_DSN"):
    import sentry_sdk
    from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration

    sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[AwsLambdaIntegration()])


logger = logging.getLogger()


def run_update():
    game = ESPNEvaluator().find_current_game()
    logger.info(f"Found current game: {game}")
    game_display = GameDisplay(game)
    rendered = render(game_display)
    upload(rendered)

    if game.has_ended():
        if should_toot():
            tooter.post_status(game_display.tweet_text)
        else:
            logger.info("Not tooting since tooting disabled")

        if should_tweet():
            tweeter.post_tweet(game_display.tweet_text)
        else:
            logger.info("Not tweeting since tweeting disabled")
    else:
        logger.info("Not posting since game not ended")


def lambda_handler(event, context):
    logger.setLevel(logging.INFO)
    if event.get("bust"):
        tweeter.bust()
        tooter.bust()
        ssm_config.bust_cache()

    run_update()
    return {"success": True}
