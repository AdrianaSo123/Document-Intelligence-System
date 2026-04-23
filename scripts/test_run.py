import os
import sys
from dotenv import load_dotenv

# Ensure Python can find the 'src' directory
sys.path.insert(0, os.path.abspath("src"))

# Load the API key from .env
load_dotenv()

from bdis.adapters.repositories import SqliteDocumentRepository, DocumentInsightModel
from bdis.frameworks.openai_extractor import OpenAIExtractor
from bdis.usecases.process_document import ProcessDocumentUseCase

def run_e2e_test():
    print("🚀 Initializing BDIS Native Test...")
    
    # 1. Setup the real repository and real OpenAI extractor
    repo = SqliteDocumentRepository("sqlite:///local_test.db")
    extractor = OpenAIExtractor(os.getenv("OPENAI_API_KEY"))
    usecase = ProcessDocumentUseCase(extractor, repo)
    
    # 2. Mock some messy, unstructured invoice text
    raw_text = """
    *** INVOICE ***
    To: Cyberdyne Systems
    Invoice Number: CYB-001
    Please remit payment of $42,500.00 by 2026-10-31.
    Status: UNPAID
    We appreciate your business. Do not ignore this.
    """
    
    print("\n📄 Sending messy text to OpenAI...")
    
    # 3. Execute the Use Case!
    try:
        doc_id = usecase.execute(raw_text)
        print(f"✅ Success! Document saved to local_test.db with ID: {doc_id}")
        
        # 4. Verify what was actually saved
        print("\n🔍 Fetching saved entity directly from Database:")
        with repo.SessionLocal() as session:
            record = session.query(DocumentInsightModel).filter_by(id=doc_id).first()
            print(f"   Company: {record.company_name}")
            print(f"   Amount:  ${record.amount_usd}")
            print(f"   Status:  {record.status}")
            print(f"   Due:     {record.due_date}")
            
    except Exception as e:
        print(f"❌ Error occurred: {str(e)}")

if __name__ == "__main__":
    run_e2e_test()
