from abc import ABC, abstractmethod
from typing import List
from bdis.domain.entities import DocumentInsight

class IDocumentRepository(ABC):
    @abstractmethod
    def save(self, insight: DocumentInsight) -> str:
        """Saves a DocumentInsight and returns its unique ID"""
        pass
        
    @abstractmethod
    def get_all(self) -> List[DocumentInsight]:
        """Retrieves all parsed documents from the data store"""
        pass
        
    @abstractmethod
    def get_all_raw(self) -> List[dict]:
        """CQRS specific read for UI models"""
        pass
