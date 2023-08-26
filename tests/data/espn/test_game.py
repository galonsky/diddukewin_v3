from ddw.models import ResultType
from ddw.data.espn.models import ESPNGame


class TestHasValidScore:
    def test_score_is_valid(self):
        assert ESPNGame(
            date="", opponent="", winlose="", urlslug="", score="100-89"
        ).has_valid_score()

    def test_empty_not_valid(self):
        assert not ESPNGame(
            date="", opponent="", winlose="", urlslug="", score=""
        ).has_valid_score()


class TestHasEnded:
    def test_w_ended(self):
        assert ESPNGame(
            date="", opponent="", winlose="W", urlslug="", score=""
        ).has_ended()

    def test_l_ended(self):
        assert ESPNGame(
            date="", opponent="", winlose="L", urlslug="", score=""
        ).has_ended()

    def test_time_not_ended(self):
        assert not ESPNGame(
            date="", opponent="", winlose="12:21 1ST", urlslug="", score=""
        ).has_ended()

    def test_empty_not_ended(self):
        assert not ESPNGame(
            date="", opponent="", winlose="", urlslug="", score=""
        ).has_ended()


class TestGetLink:
    def test_when_ended_returns_recap(self):
        assert (
            ESPNGame(
                date="", opponent="", winlose="L", urlslug="?slug", score=""
            ).get_link()
            == "http://espn.go.com/ncb/recap?slug"
        )

    def test_when_not_ended_returns_gamecast(self):
        assert (
            ESPNGame(
                date="", opponent="", winlose="", urlslug="?slug", score=""
            ).get_link()
            == "http://espn.go.com/ncb/gamecast?slug"
        )


class TestGetResultType:
    def test_when_l_returns_loss(self):
        assert (
            ESPNGame(
                date="", opponent="", winlose="L", urlslug="?slug", score=""
            ).get_result_type()
            == ResultType.LOSS
        )

    def test_when_w_returns_win(self):
        assert (
            ESPNGame(
                date="", opponent="", winlose="W", urlslug="?slug", score=""
            ).get_result_type()
            == ResultType.WIN
        )

    def test_when_empty_returns_not_yet(self):
        assert (
            ESPNGame(
                date="", opponent="", winlose="", urlslug="?slug", score=""
            ).get_result_type()
            == ResultType.NOT_YET
        )
