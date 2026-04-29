from abc import ABC, abstractmethod
from typing import List
from bdis.domain.entities import DocumentExtraction

class IDocumentRepository(ABC):
    @abstractmethod
    def save(self, workspace_id: str, extraction: DocumentExtraction) -> str:
        """Saves a DocumentExtraction and returns its unique ID"""
        pass
        
    @abstractmethod
    def get_all(self, workspace_id: str) -> List[DocumentExtraction]:
        """Retrieves all parsed documents from the data store"""
        pass

    @abstractmethod
    def get_by_document_id(self, workspace_id: str, document_id: str) -> DocumentExtraction | None:
        """Retrieve a single document extraction by workspace + document_id."""
        pass
        
    @abstractmethod
    def get_all_raw(self, workspace_id: str) -> List[dict]:
        """CQRS specific read for UI models"""
        pass
