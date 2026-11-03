from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from ddw.data.ncaa.fetcher import NCAAFetcher, NCAAThrottled


class TestFetcher:
    def test_zero_pads_date_spring(self, mocker) -> None:
        requests_mock = mocker.patch("requests.get")
        fetcher = NCAAFetcher()
        fetcher.fetch_scoreboard(
            datetime(2025, 3, 4, 1, tzinfo=ZoneInfo("America/New_York"))
        )
        requests_mock.assert_called_once_with(
            "https://sdataprod.ncaa.com/?meta=GetContests_web&extensions=%7B%22persistedQuery%22:%7B%22version%22:1,%22sha256Hash%22:%227287cda610a9326931931080cb3a604828febe6fe3c9016a7e4a36db99efdb7c%22%7D%7D&variables=%7B%22sportCode%22:%22MBB%22,%22division%22:1,%22seasonYear%22:2024,%22contestDate%22:%2203/04/2025%22,%22week%22:null%7D",
            headers=mocker.ANY,
            timeout=10,
        )

    def test_zero_pads_date_fall(self, mocker) -> None:
        requests_mock = mocker.patch("requests.get")
        fetcher = NCAAFetcher()
        fetcher.fetch_scoreboard(
            datetime(2025, 11, 4, 1, tzinfo=ZoneInfo("America/New_York"))
        )
        requests_mock.assert_called_once_with(
            "https://sdataprod.ncaa.com/?meta=GetContests_web&extensions=%7B%22persistedQuery%22:%7B%22version%22:1,%22sha256Hash%22:%227287cda610a9326931931080cb3a604828febe6fe3c9016a7e4a36db99efdb7c%22%7D%7D&variables=%7B%22sportCode%22:%22MBB%22,%22division%22:1,%22seasonYear%22:2025,%22contestDate%22:%2211/04/2025%22,%22week%22:null%7D",
            headers=mocker.ANY,
            timeout=10,
        )

    def test_sends_timeout_and_user_agent(self, mocker) -> None:
        requests_mock = mocker.patch("requests.get")
        NCAAFetcher().fetch_scoreboard(
            datetime(2025, 11, 4, 1, tzinfo=ZoneInfo("America/New_York"))
        )
        kwargs = requests_mock.call_args.kwargs
        assert kwargs["timeout"] == 10
        assert "diddukewin" in kwargs["headers"]["User-Agent"]

    @pytest.mark.parametrize("status", [403, 429])
    def test_throttle_raises_with_retry_after(self, mocker, status) -> None:
        response = mocker.MagicMock(ok=False, status_code=status)
        response.headers = {"Retry-After": "42"}
        mocker.patch("requests.get", return_value=response)
        with pytest.raises(NCAAThrottled) as exc:
            NCAAFetcher().fetch_scoreboard(datetime(2025, 11, 4, 1))
        assert exc.value.retry_after == 42

    def test_throttle_without_retry_after(self, mocker) -> None:
        response = mocker.MagicMock(ok=False, status_code=429)
        response.headers = {}
        mocker.patch("requests.get", return_value=response)
        with pytest.raises(NCAAThrottled) as exc:
            NCAAFetcher().fetch_scoreboard(datetime(2025, 11, 4, 1))
        assert exc.value.retry_after is None

    def test_other_errors_return_none(self, mocker) -> None:
        mocker.patch(
            "requests.get", return_value=mocker.MagicMock(ok=False, status_code=500)
        )
        assert NCAAFetcher().fetch_scoreboard(datetime(2025, 11, 4, 1)) is None
