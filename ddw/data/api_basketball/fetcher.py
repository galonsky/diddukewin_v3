import os
from datetime import datetime

import requests

from ddw.data.api_basketball.constants import TEAM_ID

API_BASKETBALL_HOST = "api-basketball.p.rapidapi.com"
API_URL = "https://api-basketball.p.rapidapi.com/games"


def get_season(as_of: datetime) -> str:
    if as_of.month >= 10:
        return f"{as_of.year}-{as_of.year + 1}"
    else:
        return f"{as_of.year - 1}-{as_of.year}"


class APIBasketballFetcher:
    def fetch_games(self) -> dict:
        querystring = {"season": get_season(datetime.now()), "team": str(TEAM_ID)}

        headers = {
            "X-RapidAPI-Key": os.getenv("API_BASKETBALL_KEY"),
            "X-RapidAPI-Host": API_BASKETBALL_HOST,
        }

        response = requests.get(API_URL, headers=headers, params=querystring)
        return response.json()
