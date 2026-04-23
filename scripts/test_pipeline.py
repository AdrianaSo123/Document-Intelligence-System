import os
import sys
import logging
import uuid
from dotenv import load_dotenv

# Ensure Python can find the 'src' directory
sys.path.insert(0, os.path.abspath("src"))

# Load environment variables
load_dotenv()

from bdis.usecases.processing_pipeline import ProcessingPipeline
from bdis.frameworks.openai_extractor import OpenAIExtractor
from bdis.domain.normalization import DocumentNormalizer
from bdis.adapters.repositories import SQLDocumentRepository
from bdis.adapters.evaluator_adapter import ExactMatchEvaluator
from bdis.adapters.sanitizer_adapter import RegexPIISanitizer
from bdis.core.resilience import resilience_wrapper

# Configure logging to see the pipeline steps
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def run_phase4_demo():
    print("\n🚀 Starting Phase 4 Reliability & Evaluation Demo\n" + "="*50)
    
    # 1. Setup Dependencies (Manual DI for the script)
    repo = SQLDocumentRepository("sqlite:///local_test.db")
    
    # Setup Extractor with Resilience
    raw_extractor = OpenAIExtractor(os.getenv("OPENAI_API_KEY"))
    # Wrap extraction with circuit breaker logic (as defined in dependencies.py)
    raw_extractor.extract_schema = resilience_wrapper("openai_service")(raw_extractor.extract_schema)
    
    pipeline = ProcessingPipeline(
        extractor=raw_extractor,
        normalizer=DocumentNormalizer(),
        repository=repo,
        evaluator=ExactMatchEvaluator(),
        sanitizer=RegexPIISanitizer()
    )

    # 2. Mock messier input with PII
    messy_pii_text = """
    *** INVOICE: 2026-0042 ***
    From: ACME CORP (billing@acme.com)
    To: John Doe (SSN: 123-45-6789)
    Total Due: $1,250.50 USD
    Date: October 23, 2026
    Please call 555-0199 for support.
    """

    # Ground truth for evaluation
    ground_truth = {
        "company_name": "ACME CORP",
        "amount_usd": 1250.50,
        "due_date": "2026-10-23"
    }

    print("📄 Input Text contains PII (email, SSN)...")
    print("-" * 30)
    print(messy_pii_text.strip())
    print("-" * 30)

    # 3. Execute Pipeline
    print("\n⚙️  Running Pipeline...")
    trace_id = f"test-trace-{uuid.uuid4().hex[:6]}"
    doc_id = f"test-doc-{uuid.uuid4().hex[:6]}"
    
    result = pipeline.execute(
        raw_text=messy_pii_text,
        document_id=doc_id,
        trace_id=trace_id,
        expected_data=ground_truth
    )

    # 4. Show Results
    print("\n✨ Pipeline Complete!")
    print(f"📊 Status: {result.status}")
    print(f"🎯 Confidence: {result.confidence:.2f}")
    
    print(f"\n🛡️  Sanitized Text (Verify no PII):")
    print("-" * 30)
    print(result.raw_text.strip()) # Result stores the text AFTER sanitization
    print("-" * 30)

    print(f"\n✅ Normalized Data:")
    print(f"   Company: {result.extracted_data.get('company_name')}")
    print(f"   Amount:  {result.extracted_data.get('amount_usd')}")
    print(f"   Due:     {result.extracted_data.get('due_date')}")

    if result.evaluation:
        print(f"\n📈 Evaluation Results (vs Ground Truth):")
        print(f"   Accuracy: {result.evaluation.accuracy:.2f}")
        print(f"   Scores:   {result.evaluation.field_scores}")

if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY not found in .env")
    else:
        run_phase4_demo()
