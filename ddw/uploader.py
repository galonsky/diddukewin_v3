import boto3
import hashlib
from botocore.exceptions import ClientError

BUCKET_NAME = "diddukewin.com"
KEY = "index.html"

client = boto3.client("s3")


def head_object(bucket: str, key: str) -> dict:
    try:
        return client.head_object(Bucket=bucket, Key=key)
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
        return
    return client.put_object(
        Bucket=bucket, Key=key, Body=content, ContentType="text/html"
    )
