Business Document Intelligence System (BDIS) — Phase 4 Spec
Title: Reliability, Evaluation, and Scalable Processing Layer
Objective
Upgrade BDIS from a functional AI pipeline into a reliable, observable, and scalable AI system suitable for real-world business deployment.
Phase 4 introduces:
Deterministic evaluation of AI outputs
Failure handling and recovery mechanisms
Asynchronous job processing
System observability (logging + traceability)
Confidence-aware insight generation
Core Philosophy
All AI outputs must be:
Validated, Measured, Recoverable, and Traceable.

**Professional Standards (Clean Architecture):**
- **Separation of Concerns:** Keep high-level policy away from low-level mechanisms.
- **Dependency Inversion:** All components interact through **Ports** (Interfaces).
- **Data Integrity & Privacy:** No PII should reach external LLMs without sanitization.
- **Resilience:** Use retries and **Circuit Breakers** to handle external service failures.
1. Evaluation Layer
Purpose
Quantify extraction accuracy and system performance.
Components
1.1 Ground Truth Dataset
Create a dataset of labeled documents:
{
  "document_id": "inv_001",
  "expected": {
    "company_name": "Acme Corp",
    "invoice_id": "INV-123",
    "amount": 1200.50,
    "due_date": "2024-01-01"
  }
}
Store as:
/evaluation/dataset.json
1.2 Evaluation Engine
**Port:** `IEvaluator`
File: evaluation/evaluator.py
Responsibilities:
Compare extracted output vs expected
Compute metrics:
Field-level accuracy
Missing fields
Type correctness
Exact match score
Output:
{
  "document_id": "inv_001",
  "accuracy": 0.75,
  "field_scores": {
    "company_name": true,
    "invoice_id": true,
    "amount": false,
    "due_date": true
  },
  "missing_fields": ["amount"],
  "confidence_score": 0.68
}
1.3 Aggregated Metrics
Track:
Average accuracy
Failure rate
Most error-prone fields
Store results in:
/evaluation/results.db (SQLite or Postgres)
2. Reliability & Normalization Layer
Purpose
Ensure data integrity through deterministic correction and strict validation.
2.1 Structured Output Enforcement
After LLM extraction:
1. **Normalization:** Apply deterministic corrections.
2. **Validation:** Enforce strict Pydantic schema check.
3. **Final Status:** Assign state based on validation result.
2.2 Correction & Normalization Module
**Port:** `INormalizer`
File: core/normalization.py
Strategies:
1. **Deterministic Casting:** Fix obvious type mismatches (e.g., "$1,200" → 1200.0).
2. **Schema Alignment:** Map synonymous fields to the target schema.
3. **Last Resort Re-prompt:** Only re-prompt LLM if deterministic correction fails and confidence is above 0.5.
4. **Flag for Review:** If both fail, move to `REVIEW_REQUIRED` state.
2.3 Resilience (Retry & Circuit Breaker)
Implement a resilience wrapper for external calls:
- **Retry:** Exponential backoff for transient failures (HTTP 429/500).
- **Circuit Breaker:** Stop calls to the AI Gateway if failure rate exceeds 50% in a 60s window.

```python
def extract_with_resilience(document):
    # Logic for circuit breaker + retry
    return ai_gateway.extract(document)
```
2.4 Confidence Scoring
Each extraction must return:
{
  "confidence": 0.72
}
Derived from:
number of valid fields
normalization attempts applied
evaluation history (optional)
2.5 Failure States
Define unambiguous states:
VALIDATED: Schema check passed perfectly.
REVIEW_REQUIRED: Extraction successful but requires human oversight (low confidence or normalized).
FAILED: System error or catastrophic extraction failure.
Never return raw output without a verified status.
3. Asynchronous Processing Layer
Purpose
Enable scalable document processing.
3.1 Job Queue
Use:
Redis + Celery (preferred)
OR
lightweight Python queue (if needed)
3.2 Job Model (Domain Object)
{
  "job_id": "uuid",
  "status": "JobStatus (Enum)",
  "document_id": "uuid",
  "result": "DocumentResult (Domain Model)",
  "created_at": "...",
  "updated_at": "..."
}
*Note: The API Layer must map this Domain Object to a serializable DTO.*
3.3 Worker (Pipeline Orchestrator)
The worker executes a `ProcessingPipeline` using a series of defined **Ports**:
1. **Ingestor:** Reads raw file.
2. **Sanitizer:** Scans and redacts PII before external transmission.
3. **Extractor:** Interacts with `IAIExtractor` Port.
4. **Normalizer:** Applies deterministic domain corrections.
5. **Validator:** Enforces Pydantic schema contracts.
6. **Evaluator:** Compares vs Ground Truth Port.
7. **Persistence:** Saves via `IDocumentRepository` Port.
3.4 API Endpoints (FastAPI)
POST   /jobs/create
GET    /jobs/{id}
GET    /jobs
4. Observability Layer
Purpose
Make the system debuggable and production-operable.
4.1 Structured Logging
Use JSON logs:
{
  "event": "extraction_attempt",
  "document_id": "inv_001",
  "status": "failed",
  "error": "invalid_json",
  "timestamp": "..."
}
4.2 Logging Points (Pipeline Traceability)
Log entry/exit for EVERY pipeline stage:
`[PIPELINE] [INGEST] START doc_id: 123`
`[PIPELINE] [NORMALIZER] APPLIED correction: cast_to_float on doc_id: 123`
`[PIPELINE] [VALIDATOR] FAIL error: missing_field on doc_id: 123`
4.3 Error Tracking
Store failures in:
/logs/errors.db
Track:
error type
document_id
frequency
4.4 Traceability
Each document must have:
trace_id
Used across:
logs
jobs
outputs
5. Insight Engine Upgrade
**Policy:** `InsightGenerationPolicy`
Purpose: Ensure insights are confidence-aware and reliable.
Enhancements
Only generate insights if:
confidence > threshold (e.g. 0.7)
Flag:
low-confidence documents
high-risk + low-confidence combos
Example Output
{
  "risk_flag": true,
  "reason": "High amount + overdue",
  "confidence": 0.81,
  "requires_review": false
}
6. Persistence Detail (Repository Pattern)
High-level policy must be decoupled from storage.
**Interface:** `IDocumentRepository`
**Implementation (Phase 4):** SQLite
**Implementation (Phase 5):** PostgreSQL (Dockerized)
Separate tables:
documents
extractions
evaluations
jobs
7. System Flow (Updated)
Upload Document
    ↓
Create Job
    ↓
Worker Picks Job
    ↓
Ingestion
    ↓
Sanitization (PII Check)
    ↓
LLM Extraction (via Gateway)
    ↓
Normalization (Deterministic)
    ↓
Validation (Strict)
    ↓
Evaluation
    ↓
Confidence Scoring
    ↓
Insight Generation
    ↓
Store Results (Repository)
    ↓
Return Status
8. Acceptance Criteria (Enterprise Standard)
System is complete when:
 **Port/Adapter Mapping:** 100% of external integrations (DB, AI, Redis) use Ports defined in `src/bdis/ports/`.
 **Test Coverage:** >90% unit test coverage on core domain logic.
 **Privacy:** Documentation and tests prove PII is sanitized before reaching external APIs.
 **Resilience:** System successfully handles LLM downtime via Circuit Breakers.
 **Traceability:** Every pipeline step is logged with a unique `trace_id`.
 **Performance:** API supports job pooling and async processing lifecycle.
9. Stretch Goals (if you want to go elite)
Human-in-the-loop correction UI
Feedback loop → improves prompts
Model comparison (GPT vs others)
Batch processing + rate limiting
Audit trail for compliance
