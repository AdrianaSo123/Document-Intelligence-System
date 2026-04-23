import os
from bdis.adapters.repositories import SqliteDocumentRepository
from bdis.frameworks.openai_extractor import OpenAIExtractor
from bdis.usecases.process_document import ProcessDocumentUseCase

def get_repository():
    return SqliteDocumentRepository(os.getenv("DATABASE_URL", "sqlite:///bdis_prod.db"))

def get_extractor():
    return OpenAIExtractor(os.getenv("OPENAI_API_KEY"))

def get_process_document_usecase():
    return ProcessDocumentUseCase(get_extractor(), get_repository())
