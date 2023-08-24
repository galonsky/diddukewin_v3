import pytest

from ddw.models import ResultType, GameDisplay
from ddw.data.espn.models import ESPNGame


@pytest.fixture(params=[result_type for result_type in ResultType])
def result_type(request):
    return request.param


class TestCssClass:
    def test_has_class_for_every_result(self, result_type):
        assert result_type in GameDisplay.RESULT_TO_CSS_CLASS

    def test_when_win_returns_yes(self):
        assert GameDisplay(ESPNGame("", "", "W", "", "")).css_class == "yes"


class TestResultText:
    def test_has_text_for_every_result(self, result_type):
        assert result_type in GameDisplay.RESULT_TO_TEXT

    def test_when_win_returns_yes(self):
        assert GameDisplay(ESPNGame("", "", "W", "", "")).result_text == "YES"


class TestLinkText:
    def test_returns_winlose_and_score(self):
        assert GameDisplay(ESPNGame("", "", "W", "32-31", "")).link_text == "W 32-31"


class TestTweetText:
    def test_returns_result_score_and_link(self):
        assert (
            GameDisplay(ESPNGame("", "", "W", "32-31", "")).tweet_text
            == "YES. 32-31 http://www.diddukewin.com"
        )
