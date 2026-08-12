from ddw.data.ncaa.NCAAGame import NCAAGame
from ddw.models import GameDisplay, LastKnownGame, ResultType
from ddw.renderer import parse_last_known_game, render


class TestRender:
    def test_renders_display(self):
        game = GameDisplay(NCAAGame(ResultType.LOSS, "67-70"))

        rendered = render(game)

        assert rendered.startswith("<!doctype html><html lang=en>")
        assert (
            'content="width=device-width,initial-scale=1,viewport-fit=cover"'
            in rendered
        )
        assert "<main class=no>" in rendered
        assert "<h1 class=result>NO</h1>" in rendered
        assert 'aria-label="Game result: L 67-70"' in rendered
        assert "https://bsky.app/profile/diddukewin.com" in rendered
        assert "class=social-icon" in rendered
        assert "<iframe" not in rendered
        assert "http://diddukewin.com" not in rendered
        assert 'src="http://' not in rendered
        assert '<!--ddw-state:{"result":"LOSS","score":"67-70"}-->' in rendered

    def test_parses_last_known_game_from_state_marker(self):
        game = LastKnownGame(ResultType.WIN, "80-71")
        rendered = render(GameDisplay(game))

        assert parse_last_known_game(rendered) == game

    def test_parses_last_known_game_from_legacy_html(self):
        rendered = '<html><body><p class="no">NO</p><p>L 67-70</p></body></html>'

        assert parse_last_known_game(rendered) == LastKnownGame(
            ResultType.LOSS, "67-70"
        )
