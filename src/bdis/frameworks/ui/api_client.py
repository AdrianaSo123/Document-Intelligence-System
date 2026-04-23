import os
import requests
import logging
from typing import List, Union, Optional
from bdis.frameworks.ui.view_models import DashboardViewModel, ErrorViewModel

logger = logging.getLogger(__name__)

class BdisApiClient:
    def __init__(self):
        self.base_url = os.getenv("API_BASE_URL", "http://localhost:8000")

    def fetch_all_documents(self) -> Union[List[DashboardViewModel], ErrorViewModel]:
        try:
            response = requests.get(f"{self.base_url}/documents", timeout=5)
            response.raise_for_status()
            data = response.json()
            
            # Map raw JSON into Strict View Models
            return [DashboardViewModel(**item) for item in data]
            
        except requests.exceptions.ConnectionError:
            logger.error("Failed to connect to BDIS API.")
            return ErrorViewModel(error_message="BDIS Backend is offline or unreachable.")
        except Exception as e:
            logger.error(f"Unexpected API Error: {str(e)}")
            return ErrorViewModel(error_message=f"Internal API Error: {str(e)}")

    def upload_file(self, file_bytes: bytes, filename: str) -> Optional[str]:
        try:
            import filetype
            kind = filetype.guess(file_bytes)
            if kind is None or kind.mime != "application/pdf":
                logger.error(f"Security Alert: Rejected upload of non-PDF file. Hash/Mime: {kind.mime if kind else 'Unknown'}")
                return None
                
            files = {"file": (filename, file_bytes, "application/pdf")}
            response = requests.post(f"{self.base_url}/upload", files=files, timeout=10)
            response.raise_for_status()
            return response.json().get("job_id")
        except Exception as e:
            logger.error(f"Upload failed: {str(e)}")
            return None

    def get_status(self, job_id: str) -> str:
        try:
            response = requests.get(f"{self.base_url}/status/{job_id}", timeout=5)
            if response.status_code == 200:
                return response.json().get("status", "processing")
            return "processing"
        except Exception:
            return "error"
