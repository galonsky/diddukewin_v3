from datetime import datetime
from zoneinfo import ZoneInfo

from ddw.data.ncaa.NCAAGame import NCAAGame
from ddw.models import GameDisplay, ResultType
from ddw.social import (
    card_key,
    default_meta,
    final_meta,
    game_slug,
    permalink_key,
    permalink_url,
    slug_from_page,
)

NY = ZoneInfo("America/New_York")
NOW = datetime(2026, 11, 13, 9, 0, tzinfo=NY)


def game(score="82-75", result=ResultType.WIN, start=None):
    return NCAAGame(result, score, start_time=start)


class TestGameSlug:
    def test_uses_start_date_in_eastern_time(self):
        # 01:00 UTC on the 13th is still the 12th in New York.
        start = datetime(2026, 11, 13, 1, 0, tzinfo=ZoneInfo("UTC"))
        assert game_slug(game(start=start), NOW).startswith("20261112-")

    def test_falls_back_to_now(self):
        afternoon = datetime(2026, 11, 13, 15, 0, tzinfo=NY)
        assert game_slug(game(), afternoon).startswith("20261113-")

    def test_fallback_is_stable_across_midnight_until_the_cutoff(self):
        evening = datetime(2026, 11, 12, 22, 0, tzinfo=NY)
        after_midnight = datetime(2026, 11, 13, 1, 30, tzinfo=NY)
        assert game_slug(game(), evening) == game_slug(game(), after_midnight)

    def test_is_stable_and_depends_on_result(self):
        assert game_slug(game(), NOW) == game_slug(game(), NOW)
        assert game_slug(game(), NOW) != game_slug(game("82-76"), NOW)

    def test_round_trips_through_page(self):
        slug = game_slug(game(), NOW)
        meta = final_meta(GameDisplay(game()), slug, permalink=True)
        assert slug_from_page(f'<meta content="{meta.image_url}">') == slug

    def test_no_slug_in_default_page(self):
        meta = default_meta()
        assert slug_from_page(f'<meta content="{meta.image_url}">') is None


class TestMeta:
    def test_final_meta_for_permalink(self):
        meta = final_meta(GameDisplay(game()), "20261112-abc123", permalink=True)

        assert meta.title == "Did Duke Win? Yes"
        assert meta.description == "W 82-75"
        assert meta.url == "https://diddukewin.com/g/20261112-abc123/"
        assert meta.image_url == "https://diddukewin.com/g/20261112-abc123/card.png"

    def test_final_meta_for_homepage_keeps_homepage_url(self):
        meta = final_meta(
            GameDisplay(game("68-71", ResultType.LOSS)),
            "20261112-abc123",
            permalink=False,
        )

        assert meta.title == "Did Duke Win? No"
        assert meta.url == "https://diddukewin.com/"

    def test_keys_and_urls(self):
        assert permalink_key("s") == "g/s/index.html"
        assert card_key("s") == "g/s/card.png"
        assert permalink_url("s") == "https://diddukewin.com/g/s/"
