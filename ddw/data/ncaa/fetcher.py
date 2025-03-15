from datetime import datetime

import requests


class NCAAFetcher:
    def fetch_scoreboard(self, asof: datetime) -> dict:
        return requests.get(
            f"https://data.ncaa.com/casablanca/scoreboard/basketball-men/d1/{asof.year}/{asof.month}/{asof.day}/scoreboard.json"
        ).json()
