from abc import ABC, abstractmethod

class ISanitizer(ABC):
    """
    Port for redacting sensitive information (PII) from document text.
    """
    @abstractmethod
    def sanitize(self, text: str) -> str:
        pass
