import json
import logging
import sys

from ddw.logging_config import JsonFormatter


def _record(msg="hello %s", args=("x",), exc_info=None):
    return logging.LogRecord("ddw.test", logging.INFO, __file__, 1, msg, args, exc_info)


def test_formats_as_json():
    out = json.loads(JsonFormatter().format(_record()))
    assert out["message"] == "hello x"
    assert out["level"] == "INFO"
    assert out["logger"] == "ddw.test"
    assert "timestamp" in out


def test_includes_exception():
    try:
        raise ValueError("boom")
    except ValueError:
        out = json.loads(JsonFormatter().format(_record(exc_info=sys.exc_info())))
    assert "ValueError: boom" in out["exception"]


def test_includes_extra():
    rec = _record()
    rec.game_id = 42
    assert json.loads(JsonFormatter().format(rec))["game_id"] == 42
