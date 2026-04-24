import os
from bdis.adapters.repositories import SQLDocumentRepository
from bdis.adapters.s3_storage import S3StorageAdapter
from bdis.frameworks.openai_extractor import OpenAIExtractor
from bdis.usecases.fetch_documents import FetchDocumentsUseCase
from bdis.usecases.processing_pipeline import ProcessingPipeline
from bdis.domain.normalization import DocumentNormalizer
from bdis.adapters.evaluator_adapter import ExactMatchEvaluator
from bdis.adapters.sanitizer_adapter import RegexPIISanitizer
from bdis.core.resilience import resilience_wrapper

from bdis.infrastructure.database import init_database

# Cache the session factory to avoid re-initializing on every call
_session_factory = None

def get_repository():
    global _session_factory
    if _session_factory is None:
        db_url = os.getenv("DATABASE_URL", "sqlite:///bdis_prod.db")
        _, _session_factory = init_database(db_url)
    return SQLDocumentRepository(_session_factory)

def get_storage():
    return S3StorageAdapter()

def get_extractor():
    extractor = OpenAIExtractor(os.getenv("OPENAI_API_KEY"))
    # Apply shared resilience policy for the "openai_service"
    extractor.extract_schema = resilience_wrapper("openai_service")(extractor.extract_schema)
    return extractor

def get_processing_pipeline():
    """
    Composition Root: Wires up the ProcessingPipeline with its required Adapters.
    """
    return ProcessingPipeline(
        extractor=get_extractor(),
        normalizer=DocumentNormalizer(),
        repository=get_repository(),
        evaluator=ExactMatchEvaluator(),
        sanitizer=RegexPIISanitizer()
    )

def get_fetch_documents_usecase():
    return FetchDocumentsUseCase(get_repository())
