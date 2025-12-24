from os import getenv

import boto3

endpoint_url = getenv("S3_ENDPOINT_URL")

session = boto3.session.Session()
s3 = session.client("s3", region_name="us-east-1", endpoint_url=endpoint_url)
