from abc import ABC, abstractmethod

class IFileStorage(ABC):
    @abstractmethod
    def upload_file(self, file_bytes: bytes, filename: str) -> str:
        """Uploads file to cloud storage and returns the secure URI."""
        pass
