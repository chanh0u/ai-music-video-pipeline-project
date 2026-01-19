# storage.py
import boto3
import uuid

s3 = boto3.client("s3")
BUCKET = "ai-music-mvp"

def upload_s3(file_path):
    key = f"outputs/{uuid.uuid4()}"
    s3.upload_file(file_path, BUCKET, key)
    return f"https://{BUCKET}.s3.amazonaws.com/{key}"