from abc import ABC, abstractmethod
from bdis.domain.entities import RawExtraction

class IExtractionService(ABC):
    @abstractmethod
    def extract_schema(self, raw_text: str) -> RawExtraction:
        """
        Takes raw document text and extracts structured data.
        Returns a typed RawExtraction result.
        """
        pass
