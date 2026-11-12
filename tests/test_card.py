from io import BytesIO

import pytest
from PIL import Image

from ddw.card import (
    DEFAULT_COLOR,
    HEIGHT,
    LOSS_COLOR,
    WIDTH,
    WIN_COLOR,
    render_card,
    render_default_card,
)
from ddw.models import ResultType


def decode(png: bytes) -> Image.Image:
    return Image.open(BytesIO(png)).convert("RGB")


class TestRenderCard:
    @pytest.mark.parametrize(
        "result_type, text, color",
        [
            (ResultType.WIN, "YES", WIN_COLOR),
            (ResultType.LOSS, "NO", LOSS_COLOR),
        ],
    )
    def test_is_social_sized_png_on_result_color(self, result_type, text, color):
        image = decode(render_card(result_type, text, "W 82-75"))

        assert image.size == (WIDTH, HEIGHT) == (1200, 630)
        assert image.getpixel((5, 5)) == Image.new("RGB", (1, 1), color).getpixel(
            (0, 0)
        )

    def test_draws_white_text(self):
        image = decode(render_card(ResultType.WIN, "YES", "W 82-75"))

        assert any(
            image.getpixel((x, 200)) == (255, 255, 255) for x in range(200, 1000)
        )

    def test_is_deterministic(self):
        assert render_card(ResultType.WIN, "YES", "W 82-75") == render_card(
            ResultType.WIN, "YES", "W 82-75"
        )

    def test_score_changes_the_image(self):
        assert render_card(ResultType.WIN, "YES", "W 82-75") != render_card(
            ResultType.WIN, "YES", "W 82-76"
        )

    def test_refuses_unfinished_game(self):
        with pytest.raises(ValueError):
            render_card(ResultType.NOT_YET, "NOT YET", "10-8")


def test_default_card_is_social_sized_png():
    image = decode(render_default_card())

    assert image.size == (1200, 630)
    assert image.getpixel((5, 5)) == Image.new("RGB", (1, 1), DEFAULT_COLOR).getpixel(
        (0, 0)
    )
