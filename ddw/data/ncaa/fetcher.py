import logging
from datetime import datetime
from typing import Optional

import requests

logger = logging.getLogger()

USER_AGENT = "diddukewin/3 (+https://diddukewin.com)"
TIMEOUT_SECONDS = 10


class NCAAThrottled(Exception):
    def __init__(self, status_code: int, retry_after: Optional[float] = None) -> None:
        super().__init__(f"NCAA throttled us with status {status_code}")
        self.status_code = status_code
        self.retry_after = retry_after


def _parse_retry_after(value: Optional[str]) -> Optional[float]:
    try:
        return float(value) if value else None
    except ValueError:
        return None


class NCAAFetcher:
    def fetch_scoreboard(self, asof: datetime) -> Optional[dict]:
        season_year = asof.year if asof.month > 10 else asof.year - 1
        url = f"https://sdataprod.ncaa.com/?meta=GetContests_web&extensions=%7B%22persistedQuery%22:%7B%22version%22:1,%22sha256Hash%22:%227287cda610a9326931931080cb3a604828febe6fe3c9016a7e4a36db99efdb7c%22%7D%7D&variables=%7B%22sportCode%22:%22MBB%22,%22division%22:1,%22seasonYear%22:{season_year},%22contestDate%22:%22{asof.month:02}/{asof.day:02}/{asof.year}%22,%22week%22:null%7D"
        response = requests.get(
            url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT_SECONDS
        )
        if response.ok:
            return response.json()
        logger.info(f"Got status {response.status_code} from NCAA")
        if response.status_code in (403, 429):
            raise NCAAThrottled(
                response.status_code,
                _parse_retry_after(response.headers.get("Retry-After")),
            )
        return None
