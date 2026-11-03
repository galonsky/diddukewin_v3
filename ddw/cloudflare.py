import logging
import os

import requests

logger = logging.getLogger()

API_URL = "https://api.cloudflare.com/client/v4/zones/{zone_id}/purge_cache"


def site_url() -> str:
    return os.getenv("SITE_URL", "https://diddukewin.com").rstrip("/")


def is_configured() -> bool:
    return bool(os.getenv("CLOUDFLARE_ZONE_ID") and os.getenv("CLOUDFLARE_API_TOKEN"))


def site_urls() -> list[str]:
    base = site_url()
    return [f"{base}/", f"{base}/index.html", f"{base}/score.json"]


def purge_urls(urls: list[str]) -> bool:
    """Purge URLs from the Cloudflare edge cache. Never raises; returns success."""
    if not is_configured():
        logger.info("Cloudflare not configured, skipping purge")
        return False
    try:
        response = requests.post(
            API_URL.format(zone_id=os.environ["CLOUDFLARE_ZONE_ID"]),
            headers={"Authorization": f"Bearer {os.environ['CLOUDFLARE_API_TOKEN']}"},
            json={"files": urls},
            timeout=10,
        )
    except requests.RequestException:
        logger.exception("Cloudflare purge failed")
        return False
    if not response.ok:
        logger.error(f"Cloudflare purge returned {response.status_code}")
        return False
    logger.info("Purged Cloudflare cache")
    return True


def cache_control(max_age: int) -> str:
    """Long edge TTL only when we can purge on change; otherwise keep it short."""
    s_maxage = 86400 if is_configured() else 300
    return f"public, max-age={max_age}, s-maxage={s_maxage}"
