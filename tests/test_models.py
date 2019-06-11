from models import Game


class TestHasValidScore:
    def test_score_is_valid(self):
        assert Game(
            date="", opponent="", winlose="", urlslug="", score="100-89"
        ).has_valid_score()

    def test_empty_not_valid(self):
        assert not Game(
            date="", opponent="", winlose="", urlslug="", score=""
        ).has_valid_score()


class TestHasEnded:
    def test_w_ended(self):
        assert Game(date="", opponent="", winlose="W", urlslug="", score="").has_ended()

    def test_l_ended(self):
        assert Game(date="", opponent="", winlose="L", urlslug="", score="").has_ended()

    def test_time_not_ended(self):
        assert not Game(
            date="", opponent="", winlose="12:21 1ST", urlslug="", score=""
        ).has_ended()

    def test_empty_not_ended(self):
        assert not Game(
            date="", opponent="", winlose="", urlslug="", score=""
        ).has_ended()


class TestGetLink:
    def test_when_ended_returns_recap(self):
        assert (
            Game(
                date="", opponent="", winlose="L", urlslug="?slug", score=""
            ).get_link()
            == "http://espn.go.com/ncb/recap?slug"
        )

    def test_when_not_ended_returns_gamecast(self):
        assert (
            Game(date="", opponent="", winlose="", urlslug="?slug", score="").get_link()
            == "http://espn.go.com/ncb/gamecast?slug"
        )
