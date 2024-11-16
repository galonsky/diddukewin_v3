import logging
import os
from dataclasses import dataclass
from datetime import datetime

from atproto import Client
from atproto_client.models.app.bsky.actor.defs import ProfileViewDetailed
from atproto_client.models.app.bsky.feed.post import Record
from atproto_client.utils import TextBuilder

from ddw.models import Status


logger = logging.getLogger()
MIN_HOURS_BETWEEN_SKEETS = int(os.getenv("MIN_HOURS_BETWEEN_SKEETS", 8))


class Skeet(Status):
    @classmethod
    def from_record(cls, record: Record) -> "Skeet":
        return cls(
            content=record.text,
            created_at=datetime.fromisoformat(record.created_at),
        )


class Skeeter:
    def __init__(
        self, username: str | None = None, password: str | None = None
    ) -> None:
        self.username = username or os.getenv("BLUESKY_USERNAME")
        self.password = password or os.getenv("BLUESKY_PASSWORD")

    def post_skeet(self, text: str) -> None:
        client = Client()
        profile_view = client.login(self.username, self.password)
        latest_skeet = self._get_latest_skeet(client, profile_view)
        if latest_skeet:
            logger.info(f"Found latest skeet: {latest_skeet.text_without_link}")

            if latest_skeet.hours_ago <= MIN_HOURS_BETWEEN_SKEETS:
                logger.info("Too soon, not skeeting.")
                return

            new_toot = Skeet(created_at=datetime.now(), content=text)
            if latest_skeet.text_without_link == new_toot.text_without_link:
                logger.info("Same content, not skeeting.")
                return
        tb = TextBuilder()
        tb.link(text, "https://diddukewin.com")
        client.send_post(text=tb, langs=["en-US"])
        logger.info(f"Posted skeet: {text}")

    @staticmethod
    def _get_latest_skeet(
        client: Client, profile_view: ProfileViewDetailed
    ) -> Skeet | None:
        feed_response = client.get_author_feed(actor=profile_view.did, limit=1)
        if not feed_response.feed:
            return None

        return Skeet.from_record(feed_response.feed[0].post.record)


skeeter = Skeeter()
