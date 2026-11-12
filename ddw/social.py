"""Link-preview metadata and the per-game permalink that carries it."""

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from ddw.cloudflare import site_url
from ddw.models import GameDisplay, IGame

DEFAULT_TITLE = "Did Duke Win?"
DEFAULT_DESCRIPTION = "The latest Duke basketball result, at a glance."
DEFAULT_CARD_KEY = "cards/default.png"
# The evaluator keeps returning a finished game until 06:00 ET.
FINISHED_GAME_CUTOFF = timedelta(hours=6)
PERMALINK_CACHE_CONTROL = "public, max-age=31536000, immutable"


@dataclass(frozen=True)
class SocialMeta:
    title: str
    description: str
    url: str
    image_url: str
    image_alt: str


def game_slug(game: IGame, now: datetime) -> str:
    """Stable id for a finished game: its date plus a hash of the result.

    IGame carries no game id, so date and final score stand in for one. Without
    a start time the date comes from `now`, shifted back by the evaluator's
    06:00 cutoff for a finished game, so polls after midnight keep the slug."""
    start = game.get_start_time() or now - FINISHED_GAME_CUTOFF
    day = start.astimezone(ZoneInfo("America/New_York")).strftime("%Y%m%d")
    digest = hashlib.md5(
        f"{game.get_result_type().name}:{game.get_score()}".encode()
    ).hexdigest()[:6]
    return f"{day}-{digest}"


def permalink_key(slug: str) -> str:
    return f"g/{slug}/index.html"


def card_key(slug: str) -> str:
    return f"g/{slug}/card.png"


def permalink_url(slug: str) -> str:
    return f"{site_url()}/g/{slug}/"


def default_meta() -> SocialMeta:
    return SocialMeta(
        title=DEFAULT_TITLE,
        description=DEFAULT_DESCRIPTION,
        url=f"{site_url()}/",
        image_url=f"{site_url()}/{DEFAULT_CARD_KEY}",
        image_alt=DEFAULT_TITLE,
    )


def result_title(game_display: GameDisplay) -> str:
    return f"Did Duke Win? {game_display.result_text.title()}"


def final_meta(game_display: GameDisplay, slug: str, *, permalink: bool) -> SocialMeta:
    """Meta for a finished game's card; `permalink` picks the game URL over the homepage."""
    title = result_title(game_display)
    description = game_display.link_text
    return SocialMeta(
        title=title,
        description=description,
        url=permalink_url(slug) if permalink else f"{site_url()}/",
        image_url=f"{site_url()}/{card_key(slug)}",
        image_alt=f"{title}. {description}",
    )


_CARD_URL_PATTERN = re.compile(r"/g/(?P<slug>\d{8}-[0-9a-f]{6})/card\.png")


def slug_from_page(content: str) -> str | None:
    """The game slug a previously uploaded page's og:image points at, if any."""
    match = _CARD_URL_PATTERN.search(content)
    return match.group("slug") if match else None
