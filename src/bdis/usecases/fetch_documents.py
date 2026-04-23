from typing import List
from bdis.ports.document_repository import IDocumentRepository

class FetchDocumentsUseCase:
    """CQRS pattern isolate to prevent FastAPI from interacting with un-abstracted SQL sessions"""
    def __init__(self, repository: IDocumentRepository):
        self.repository = repository
        
    def execute(self) -> List[dict]:
        records = self.repository.get_all_raw()
        for r in records:
            if r["due_date"]:
                r["due_date"] = r["due_date"].isoformat()
        return records
