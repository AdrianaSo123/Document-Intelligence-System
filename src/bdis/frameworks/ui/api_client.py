import os
import requests
import logging
from typing import List, Union, Optional
from bdis.frameworks.ui.view_models import DashboardViewModel, ErrorViewModel

logger = logging.getLogger(__name__)

class BdisApiClient:
    """
    Clean Architecture Bridge: Communicates with the BDIS Backend.
    Uses strict View Models to isolate the UI from API schema changes.
    """
    def __init__(self, user_id: str | None = None, workspace_id: str | None = None, role: str | None = None):
        self.base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
        self.user_id = user_id or os.getenv("BDIS_UI_USER_ID", "dev-user")
        self.workspace_id = workspace_id or os.getenv("BDIS_UI_WORKSPACE_ID", "dev-workspace")
        self.role = role or os.getenv("BDIS_UI_ROLE")

    def set_workspace(self, workspace_id: str):
        self.workspace_id = workspace_id

    def _headers(self) -> dict:
        # Phase 6B dev_headers mode
        return {
            "X-BDIS-User-Id": self.user_id,
            "X-BDIS-Workspace-Id": self.workspace_id,
            **({"X-BDIS-Role": self.role} if self.role else {}),
        }

    def list_workspaces(self):
        try:
            response = requests.get(f"{self.base_url}/workspaces/me", headers=self._headers(), timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception:
            return []

    def list_jobs(self):
        try:
            response = requests.get(
                f"{self.base_url}/workspaces/{self.workspace_id}/jobs",
                headers=self._headers(),
                timeout=5,
            )
            response.raise_for_status()
            return response.json()
        except Exception:
            return []

    def list_members(self):
        try:
            response = requests.get(
                f"{self.base_url}/workspaces/{self.workspace_id}/members",
                headers=self._headers(),
                timeout=5,
            )
            response.raise_for_status()
            return response.json()
        except Exception:
            return []

    def add_member(self, user_id: str, role: str = "ANALYST", email: str | None = None) -> bool:
        try:
            payload = {"user_id": user_id, "role": role, "email": email}
            response = requests.post(
                f"{self.base_url}/workspaces/{self.workspace_id}/members",
                headers=self._headers(),
                json=payload,
                timeout=5,
            )
            response.raise_for_status()
            return True
        except Exception:
            return False

    def fetch_all_documents(self) -> Union[List[DashboardViewModel], ErrorViewModel]:
        try:
            response = requests.get(f"{self.base_url}/workspaces/{self.workspace_id}/documents", headers=self._headers(), timeout=5)
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
            # Boundary Protection: Validate file type before sending
            import filetype
            kind = filetype.guess(file_bytes)
            if kind is None or kind.mime != "application/pdf":
                logger.error(f"Security Alert: Rejected upload of non-PDF file.")
                return None
                
            files = {"file": (filename, file_bytes, "application/pdf")}
            # Updated to match consolidated router path
            response = requests.post(f"{self.base_url}/workspaces/{self.workspace_id}/jobs", headers=self._headers(), files=files, timeout=10)
            response.raise_for_status()
            return response.json().get("job_id")
        except Exception as e:
            logger.error(f"Upload failed: {str(e)}")
            return None

    def get_status(self, job_id: str) -> str:
        try:
            # Updated to match consolidated router path
            response = requests.get(f"{self.base_url}/workspaces/{self.workspace_id}/jobs/{job_id}", headers=self._headers(), timeout=5)
            if response.status_code == 200:
                return response.json().get("status", "processing")
            return "processing"
        except Exception:
            return "error"
