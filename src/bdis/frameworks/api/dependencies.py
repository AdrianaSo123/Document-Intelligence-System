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

from bdis.core.resilience import resilience_wrapper

def get_extractor():
    extractor = OpenAIExtractor(os.getenv("OPENAI_API_KEY"))
    # Apply shared resilience policy for the "openai_service"
    extractor.extract_schema = resilience_wrapper("openai_service")(extractor.extract_schema)
    return extractor

def get_process_document_usecase():
    # Note: Phase 4 uses ProcessingPipeline, we should update this
    from bdis.usecases.processing_pipeline import ProcessingPipeline
    from bdis.domain.normalization import DocumentNormalizer
    from bdis.adapters.evaluator_adapter import ExactMatchEvaluator
    from bdis.adapters.sanitizer_adapter import RegexPIISanitizer
    
    return ProcessingPipeline(
        get_extractor(),
        DocumentNormalizer(),
        get_repository(),
        ExactMatchEvaluator(),
        RegexPIISanitizer()
    )

def get_fetch_documents_usecase():
    return FetchDocumentsUseCase(get_repository())
