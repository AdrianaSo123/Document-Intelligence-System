from abc import ABC, abstractmethod

class IFileStorage(ABC):
    @abstractmethod
    def upload_file(self, workspace_id: str, document_id: str, file_bytes: bytes, filename: str) -> str:
        """Uploads file to cloud storage and returns the secure URI."""
        pass

    @abstractmethod
    def download_file(self, s3_uri: str) -> bytes:
        """Retrieves file bytes from the given URI."""
        pass
