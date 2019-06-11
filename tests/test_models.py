from models import Game


class TestHasValidScore:
    def test_score_is_valid(self):
        assert Game(
            date='',
            opponent='',
            winlose='',
            urlslug='',
            score='100-89',
        ).has_valid_score()

    def test_empty_not_valid(self):
        assert not Game(
            date='',
            opponent='',
            winlose='',
            urlslug='',
            score='',
        ).has_valid_score()


class TestHasEnded:
    def test_w_ended(self):
        assert Game(
            date='',
            opponent='',
            winlose='W',
            urlslug='',
            score='',
        ).has_ended()

    def test_l_ended(self):
        assert Game(
            date='',
            opponent='',
            winlose='L',
            urlslug='',
            score='',
        ).has_ended()

    def test_time_not_ended(self):
        assert not Game(
            date='',
            opponent='',
            winlose='12:21 1ST',
            urlslug='',
            score='',
        ).has_ended()

    def test_empty_not_ended(self):
        assert not Game(
            date='',
            opponent='',
            winlose='',
            urlslug='',
            score='',
        ).has_ended()