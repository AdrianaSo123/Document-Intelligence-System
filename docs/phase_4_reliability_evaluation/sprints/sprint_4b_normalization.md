# Sprint 4B: The Normalization Pipeline & Resilience

**Goal:** Secure the data pipeline against PII leaks and implement deterministic correction strategies to handle "messy" LLM outputs.

## 🎯 Deliverables

1.  **The `Sanitizer` (PII Scrubber):**
    *   Implement a pipeline step to identify and redact sensitive data (PII) before it is sent to external LLM gateways.
    *   Focus: Regex-based scrubbing for SSNs, credit cards, and sensitive phone numbers.

2.  **The `INormalizer` Port:**
    *   Define the interface in `src/bdis/ports/normalizer.py`.
    *   Methods: `normalize(raw_data: dict) -> dict`.

3.  **Deterministic Correction Logic:**
    *   Implement `src/bdis/domain/normalization.py`.
    *   Logic: Data type casting (strings to floats), date formatting (ISO 8601), and schema field alignment.

4.  **Resilience (Circuit Breaker & Retry):**
    *   Implement the `ResilienceWrapper` using `tenacity` or custom logic.
    *   Enforce exponential backoff for 429/500 errors.
    *   Integrate a basic Circuit Breaker to halt AI calls if failure rates spike.

## ✅ Definition of Done
- Unit tests prove that PII is redacted from a sample document.
- Messy data (e.g., "$1,200.50") is successfully normalized to a float (1200.5).
- Circuit breaker state transitions are verified through simulated failure tests.
