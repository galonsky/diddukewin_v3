import hashlib
from os import getenv

from botocore.exceptions import ClientError
import logging

from ddw.aws import s3

logger = logging.getLogger()

BUCKET_NAME = getenv("BUCKET_NAME", "diddukewin.com")
KEY = "index.html"
SCORE_KEY = "score.json"
DEFAULT_CACHE_CONTROL = "public, max-age=60, s-maxage=300"


def head_object(bucket: str, key: str) -> dict:
    try:
        return s3.head_object(Bucket=bucket, Key=key)
    except ClientError:
        return {}


def download(bucket: str = BUCKET_NAME, key: str = KEY) -> str | None:
    try:
        response = s3.get_object(Bucket=bucket, Key=key)
        content = response["Body"].read()
        return content.decode("utf-8") if isinstance(content, bytes) else content
    except ClientError:
        return None


def md5_content(content: str | bytes) -> str:
    md5 = hashlib.md5()
    md5.update(content if isinstance(content, bytes) else content.encode("utf-8"))
    return md5.hexdigest()


def should_upload_new(content: str | bytes, bucket: str, key: str) -> bool:
    head = head_object(bucket, key)
    etag = head.get("ETag", "").strip('"')  # s3 leaves double quotes in
    return (not etag) or md5_content(content) != etag


def upload(
    content: str | bytes,
    bucket: str = BUCKET_NAME,
    key: str = KEY,
    force: bool = False,
    content_type: str = "text/html",
    cache_control: str | None = None,
) -> bool:
    """Upload content, skipping when unchanged. Returns True if it uploaded."""
    if not force and not should_upload_new(content, bucket, key):
        logger.info("Content hasn't changed, skipping upload.")
        return False
    logger.info("Uploading new file")
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=content,
        ContentType=content_type,
        CacheControl=cache_control or DEFAULT_CACHE_CONTROL,
    )
    logger.info("Upload complete")
    return True
