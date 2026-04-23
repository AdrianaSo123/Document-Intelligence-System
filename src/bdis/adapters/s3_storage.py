import os
import boto3
import uuid
import logging
from botocore.exceptions import ClientError
from bdis.ports.file_storage import IFileStorage

class S3StorageAdapter(IFileStorage):
    def __init__(self):
        self.bucket = os.getenv("S3_BUCKET_NAME", "bdis-invoices")
        try:
            self.s3_client = boto3.client(
                "s3",
                endpoint_url=os.getenv("AWS_ENDPOINT_URL"),
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1")
            )
            self.s3_client.create_bucket(Bucket=self.bucket)
        except ClientError:
            # Bucket might already exist
            pass
        except Exception as e:
            logging.error(f"Failed to connect to S3 emulator: {e}")

    def upload_file(self, file_bytes: bytes, filename: str) -> str:
        try:
            unique_name = f"{uuid.uuid4()}_{filename}"
            self.s3_client.put_object(Bucket=self.bucket, Key=unique_name, Body=file_bytes)
            return f"s3://{self.bucket}/{unique_name}"
        except Exception as e:
            logging.error(f"S3 Upload failed: {e}")
            return None
