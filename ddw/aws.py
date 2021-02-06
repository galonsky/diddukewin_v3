import boto3


session = boto3.session.Session()
s3 = session.client("s3")
ssm = session.client("ssm")
