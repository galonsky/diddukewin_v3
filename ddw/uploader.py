import boto3


BUCKET_NAME = "diddukewin.com"
KEY = "index.html"

client = boto3.client("s3")


def upload(content, bucket: str = BUCKET_NAME, key: str = KEY):
    return client.put_object(
        Bucket=bucket, Key=key, Body=content, ContentType="text/html"
    )
