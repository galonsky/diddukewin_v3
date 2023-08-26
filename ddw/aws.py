import boto3


session = boto3.session.Session()
s3 = session.client("s3", region_name="us-east-1")
