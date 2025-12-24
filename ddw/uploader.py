import hashlib
from os import getenv

from botocore.exceptions import ClientError
import logging

from ddw.aws import s3

logger = logging.getLogger()

BUCKET_NAME = getenv("BUCKET_NAME", "diddukewin.com")
KEY = "index.html"


def head_object(bucket: str, key: str) -> dict:
    try:
        return s3.head_object(Bucket=bucket, Key=key)
    except ClientError:
        return {}


def md5_content(content: str) -> str:
    md5 = hashlib.md5()
    md5.update(content.encode("utf-8"))
    return md5.hexdigest()


def should_upload_new(content: str, bucket: str, key: str) -> bool:
    head = head_object(bucket, key)
    etag = head.get("ETag", "").strip('"')  # s3 leaves double quotes in
    return (not etag) or md5_content(content) != etag


def upload(content: str, bucket: str = BUCKET_NAME, key: str = KEY):
    if not should_upload_new(content, bucket, key):
        logger.info("Content hasn't changed, skipping upload.")
        return
    logger.info("Uploading new file")
    s3.put_object(Bucket=bucket, Key=key, Body=content, ContentType="text/html")
    logger.info("Upload complete")
