"""Social card images (1200x630 PNG), drawn at publish time so the site stays static."""

from functools import lru_cache
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from ddw.models import ResultType

WIDTH = 1200
HEIGHT = 630
FONT_PATH = Path(__file__).parent / "static_files" / "fonts" / "Inter.ttf"

WIN_COLOR = "#168143"
LOSS_COLOR = "#cf2e36"
DEFAULT_COLOR = "#001a57"
TEXT_COLOR = "#ffffff"
FOOTER_COLOR = "#ffffffcc"
FOOTER_TEXT = "diddukewin.com"

RESULT_COLORS = {ResultType.WIN: WIN_COLOR, ResultType.LOSS: LOSS_COLOR}


@lru_cache(maxsize=None)
def _font(size: int, weight: int) -> ImageFont.FreeTypeFont:
    font = ImageFont.truetype(str(FONT_PATH), size)
    font.set_variation_by_axes([32, weight])  # optical size, weight
    return font


def _draw(background: str, word: str, subtitle: str | None, word_size: int) -> bytes:
    image = Image.new("RGB", (WIDTH, HEIGHT), background)
    draw = ImageDraw.Draw(image)
    center_x = WIDTH / 2

    word_font = _font(word_size, 850)
    if subtitle:
        # anchor "ms" puts the baseline at y, so the visual gap stays the same
        # whatever the word's letters are.
        draw.text((center_x, 385), word, font=word_font, fill=TEXT_COLOR, anchor="ms")
        draw.text(
            (center_x, 385 + 85),
            subtitle,
            font=_font(62, 600),
            fill=TEXT_COLOR,
            anchor="ms",
        )
    else:
        draw.text(
            (center_x, HEIGHT / 2 + word_size * 0.36),
            word,
            font=word_font,
            fill=TEXT_COLOR,
            anchor="ms",
        )
    draw.text(
        (center_x, HEIGHT - 48),
        FOOTER_TEXT,
        font=_font(36, 600),
        fill=FOOTER_COLOR,
        anchor="ms",
    )

    out = BytesIO()
    image.save(out, format="PNG", optimize=True)
    return out.getvalue()


def render_card(result_type: ResultType, result_text: str, score_text: str) -> bytes:
    """Card for a final result: YES/NO on the result colour with the score below."""
    if result_type not in RESULT_COLORS:
        raise ValueError(f"No card for an unfinished game: {result_type}")
    return _draw(RESULT_COLORS[result_type], result_text, score_text, 408)


def render_default_card() -> bytes:
    """Generic card for pages that don't show a final result yet."""
    return _draw(DEFAULT_COLOR, "Did Duke Win?", None, 150)
