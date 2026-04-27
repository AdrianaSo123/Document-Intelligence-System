import os
import boto3
import uuid
import logging
from botocore.exceptions import ClientError
from bdis.core.config import settings
from bdis.ports.file_storage import IFileStorage

class S3StorageAdapter(IFileStorage):
    def __init__(self):
        self.bucket = settings.S3_BUCKET_NAME
        self._bucket_checked = False
        try:
            self.s3_client = boto3.client(
                "s3",
                endpoint_url=os.getenv("AWS_ENDPOINT_URL"), # Keeping this for Minio local override if needed, or I could add to settings
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                region_name=settings.AWS_REGION
            )
        except Exception as e:
            logging.error(f"Failed to initialize S3 client: {e}")

    def _ensure_bucket_exists(self):
        """Lazy check to ensure bucket exists without blocking constructor."""
        if self._bucket_checked:
            return
        try:
            self.s3_client.head_bucket(Bucket=self.bucket)
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                try:
                    self.s3_client.create_bucket(Bucket=self.bucket)
                    logging.info(f"Created S3 bucket: {self.bucket}")
                except Exception as create_err:
                    logging.error(f"Could not create bucket: {create_err}")
        except Exception as e:
            logging.error(f"Error checking bucket: {e}")
        finally:
            self._bucket_checked = True

    def upload_file(self, file_bytes: bytes, filename: str) -> str:
        unique_name = f"{uuid.uuid4()}_{filename}"
        try:
            self._ensure_bucket_exists()
            self.s3_client.put_object(Bucket=self.bucket, Key=unique_name, Body=file_bytes)
            return f"s3://{self.bucket}/{unique_name}"
        except Exception as e:
            logging.warning(f"S3 Upload failed (falling back to local): {e}")
            # Fallback to local filesystem storage for portfolio/local dev
            local_path = os.path.join("storage", unique_name)
            os.makedirs("storage", exist_ok=True)
            with open(local_path, "wb") as f:
                f.write(file_bytes)
            return f"local://{local_path}"

    def download_file(self, uri: str) -> bytes:
        try:
            if uri.startswith("local://"):
                path = uri.replace("local://", "")
                with open(path, "rb") as f:
                    return f.read()
                    
            if not uri.startswith("s3://"):
                raise ValueError("Invalid URI scheme")
            
            parts = uri.replace("s3://", "").split("/", 1)
            bucket = parts[0]
            key = parts[1]
            
            response = self.s3_client.get_object(Bucket=bucket, Key=key)
            return response['Body'].read()
        except Exception as e:
            logging.error(f"Storage Download failed for {uri}: {e}")
            return None
