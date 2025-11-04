from ddw.data.ncaa.NCAAGame import NCAAGame
from ddw.models import GameDisplay, ResultType
from ddw.renderer import render


class TestRender:
    def test_renders_display(self):
        with open("tests/test_data/rendered.html", "r") as file:
            game = GameDisplay(NCAAGame(ResultType.LOSS, "67-70"))
            assert render(game) == file.read()
