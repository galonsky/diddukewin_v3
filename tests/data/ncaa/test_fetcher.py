from datetime import datetime
from zoneinfo import ZoneInfo

from ddw.data.ncaa.fetcher import NCAAFetcher


class TestFetcher:
    def test_zero_pads_date(self, mocker) -> None:
        requests_mock = mocker.patch("requests.get")
        fetcher = NCAAFetcher()
        fetcher.fetch_scoreboard(
            datetime(2025, 3, 4, 1, tzinfo=ZoneInfo("America/New_York"))
        )
        requests_mock.assert_called_once_with(
            "https://data.ncaa.com/casablanca/scoreboard/basketball-men/d1/2025/03/04/scoreboard.json"
        )
