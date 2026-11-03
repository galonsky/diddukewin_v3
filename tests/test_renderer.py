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


class TestRenderState:
    def test_live_state(self):
        import json

        from ddw.renderer import render_state

        game = NCAAGame(ResultType.NOT_YET, "40-38", period="2ND HALF", clock="5:12")
        assert json.loads(render_state(GameDisplay(game))) == {
            "result": "NOT_YET",
            "result_text": "NOT YET",
            "css_class": "notyet",
            "link_text": " 40-38",
            "period": "2ND HALF",
            "clock": "5:12",
        }

    def test_last_known_game_has_empty_period(self):
        import json

        from ddw.renderer import render_state

        state = json.loads(
            render_state(GameDisplay(LastKnownGame(ResultType.WIN, "80-71")))
        )
        assert state["period"] == "" and state["result_text"] == "YES"

    def test_live_page_includes_poll_script_but_final_does_not(self):
        live = render(GameDisplay(NCAAGame(ResultType.NOT_YET, "1-0")))
        final = render(GameDisplay(NCAAGame(ResultType.WIN, "1-0")))
        assert "/score.json" in live
        assert "/score.json" not in final
