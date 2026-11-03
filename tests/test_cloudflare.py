import requests

from ddw import cloudflare


def test_noop_without_config(mocker, monkeypatch):
    monkeypatch.delenv("CLOUDFLARE_ZONE_ID", raising=False)
    monkeypatch.delenv("CLOUDFLARE_API_TOKEN", raising=False)
    post = mocker.patch("requests.post")
    assert cloudflare.purge_urls(["https://x/"]) is False
    post.assert_not_called()


def test_purges_with_config(mocker, monkeypatch):
    monkeypatch.setenv("CLOUDFLARE_ZONE_ID", "zone1")
    monkeypatch.setenv("CLOUDFLARE_API_TOKEN", "tok")
    post = mocker.patch("requests.post", return_value=mocker.MagicMock(ok=True))
    assert cloudflare.purge_urls(["https://x/"]) is True
    post.assert_called_once_with(
        "https://api.cloudflare.com/client/v4/zones/zone1/purge_cache",
        headers={"Authorization": "Bearer tok"},
        json={"files": ["https://x/"]},
        timeout=10,
    )


def test_failures_do_not_raise(mocker, monkeypatch):
    monkeypatch.setenv("CLOUDFLARE_ZONE_ID", "zone1")
    monkeypatch.setenv("CLOUDFLARE_API_TOKEN", "tok")
    mocker.patch("requests.post", side_effect=requests.ConnectionError)
    assert cloudflare.purge_urls(["https://x/"]) is False
    mocker.patch("requests.post", return_value=mocker.MagicMock(ok=False))
    assert cloudflare.purge_urls(["https://x/"]) is False


def test_cache_control_short_ttl_when_unconfigured(monkeypatch):
    monkeypatch.delenv("CLOUDFLARE_ZONE_ID", raising=False)
    assert cloudflare.cache_control(15) == "public, max-age=15, s-maxage=300"


def test_cache_control_long_ttl_when_configured(monkeypatch):
    monkeypatch.setenv("CLOUDFLARE_ZONE_ID", "z")
    monkeypatch.setenv("CLOUDFLARE_API_TOKEN", "t")
    assert cloudflare.cache_control(5) == "public, max-age=5, s-maxage=86400"
