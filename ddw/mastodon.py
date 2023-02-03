import logging
import os
from datetime import datetime
from typing import Optional
from uuid import uuid4

import requests

from ddw.config import get_config_value
from ddw.models import Status

POST_STATUS_URL = "https://botsin.space/api/v1/statuses"
GET_STATUSES_URL = (
    "https://botsin.space/api/v1/accounts/109802258825144908/statuses?limit=1"
)
MIN_HOURS_BETWEEN_TOOTS = int(os.getenv("MIN_HOURS_BETWEEN_TOOTS", 8))


logger = logging.getLogger()


class Tooter:
    def __init__(self):
        self._access_token: Optional[str] = None
        self._last_status: Optional[Status] = None

    def bust(self) -> None:
        self._access_token = None
        self._last_status = None

    def get_latest_status(self) -> Optional[Status]:
        if self._last_status:
            return self._last_status
        statuses = requests.get(GET_STATUSES_URL).json()
        if statuses:
            status_dict = {
                "created_at": statuses[0]["created_at"],
                "content": statuses[0]["content"],
            }
            self._last_status = Status.from_status_dict(status_dict)
            return self._last_status
        return None

    def post_status(self, text: str) -> None:
        if not self._access_token:
            self._access_token = get_config_value("MASTODON_ACCESS_TOKEN")

        latest_status = self.get_latest_status()
        if latest_status:
            logger.info(f"Found latest toot: {latest_status.text_without_link}")

            if latest_status.hours_ago <= MIN_HOURS_BETWEEN_TOOTS:
                logger.info("Too soon, not tooting.")
                return

            new_toot = Status(created_at=datetime.now(), content=text)
            if latest_status.text_without_link == new_toot.text_without_link:
                logger.info("Same content, not tooting.")
                return

        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Idempotency-Key": str(uuid4()),
        }
        data = {
            "status": text,
        }

        requests.post(POST_STATUS_URL, data=data, headers=headers)
        self._last_status = None
        logger.info(f"Posted tweet: {text}")


tooter = Tooter()
