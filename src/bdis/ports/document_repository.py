from abc import ABC, abstractmethod
from typing import Optional
from bdis.domain.entities import DocumentInsight

class IDocumentRepository(ABC):
    @abstractmethod
    def save(self, insight: DocumentInsight) -> str:
        """
        Persists a DocumentInsight entity.
        Returns the ID of the saved document.
        """
        pass
