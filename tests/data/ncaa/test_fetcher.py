from datetime import datetime
from zoneinfo import ZoneInfo

from ddw.data.ncaa.fetcher import NCAAFetcher


class TestFetcher:
    def test_zero_pads_date_spring(self, mocker) -> None:
        requests_mock = mocker.patch("requests.get")
        fetcher = NCAAFetcher()
        fetcher.fetch_scoreboard(
            datetime(2025, 3, 4, 1, tzinfo=ZoneInfo("America/New_York"))
        )
        requests_mock.assert_called_once_with(
            "https://sdataprod.ncaa.com/?meta=GetContests_web&extensions=%7B%22persistedQuery%22:%7B%22version%22:1,%22sha256Hash%22:%227287cda610a9326931931080cb3a604828febe6fe3c9016a7e4a36db99efdb7c%22%7D%7D&variables=%7B%22sportCode%22:%22MBB%22,%22division%22:1,%22seasonYear%22:2024,%22contestDate%22:%2203/04/2025%22,%22week%22:null%7D"
        )

    def test_zero_pads_date_fall(self, mocker) -> None:
        requests_mock = mocker.patch("requests.get")
        fetcher = NCAAFetcher()
        fetcher.fetch_scoreboard(
            datetime(2025, 11, 4, 1, tzinfo=ZoneInfo("America/New_York"))
        )
        requests_mock.assert_called_once_with(
            "https://sdataprod.ncaa.com/?meta=GetContests_web&extensions=%7B%22persistedQuery%22:%7B%22version%22:1,%22sha256Hash%22:%227287cda610a9326931931080cb3a604828febe6fe3c9016a7e4a36db99efdb7c%22%7D%7D&variables=%7B%22sportCode%22:%22MBB%22,%22division%22:1,%22seasonYear%22:2025,%22contestDate%22:%2211/04/2025%22,%22week%22:null%7D"
        )
