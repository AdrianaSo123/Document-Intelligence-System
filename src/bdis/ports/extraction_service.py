from abc import ABC, abstractmethod

class IExtractionService(ABC):
    @abstractmethod
    def extract_schema(self, raw_text: str) -> dict:
        """
        Takes raw document text and extracts structured data.
        Returns a dictionary representation of the structured data.
        """
        pass
