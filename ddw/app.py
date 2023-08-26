import os

from ddw.evaluator import IEvaluator
from ddw.mastodon import tooter
from ddw.twitter import tweeter
from ddw.config import should_tweet, should_toot
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
    evaluator: IEvaluator = ESPNEvaluator()
    game = evaluator.find_current_game()
    if not game:
        logger.info("No game found, exiting")
        return

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


if __name__ == "__main__":
    run_update()
