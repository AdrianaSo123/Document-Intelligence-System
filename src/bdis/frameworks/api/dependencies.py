import os
from bdis.adapters.repositories import SQLDocumentRepository
from bdis.adapters.s3_storage import S3StorageAdapter
from bdis.frameworks.openai_extractor import OpenAIExtractor
from bdis.usecases.process_document import ProcessDocumentUseCase
from bdis.usecases.fetch_documents import FetchDocumentsUseCase

def get_repository():
    return SQLDocumentRepository(os.getenv("DATABASE_URL", "sqlite:///bdis_prod.db"))

def get_storage():
    return S3StorageAdapter()

def get_extractor():
    return OpenAIExtractor(os.getenv("OPENAI_API_KEY"))

def get_process_document_usecase():
    return ProcessDocumentUseCase(get_extractor(), get_repository(), get_storage())

def get_fetch_documents_usecase():
    return FetchDocumentsUseCase(get_repository())
