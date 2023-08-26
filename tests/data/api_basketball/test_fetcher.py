from datetime import datetime

from ddw.data.api_basketball.fetcher import get_season


class TestGetSeason:
    def test_october(self):
        assert get_season(datetime(2022, 10, 1)) == "2022-2023"

    def test_september(self):
        assert get_season(datetime(2022, 9, 1)) == "2021-2022"
