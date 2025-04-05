import logging
from datetime import datetime
from typing import Optional

import requests


logger = logging.getLogger()


class NCAAFetcher:
    def fetch_scoreboard(self, asof: datetime) -> Optional[dict]:
        response = requests.get(
            f"https://data.ncaa.com/casablanca/scoreboard/basketball-men/d1/{asof.year}/{asof.month:02}/{asof.day:02}/scoreboard.json"
        )
        if response.ok:
            return response.json()
        logger.info(f"Got status {response.status_code} from NCAA")
        return None
