# Sprint 3: AI Extraction Plugin & Security

**Goal:** Implement the external drivers that will parse text and consult the Large Language Model.

## 🎯 Deliverables

1. **OCR / Text Ingestion:**
   - Implement `pdfplumber` for native PDF text extraction.
   - Implement fallback to `pytesseract` or `EasyOCR` if the document is an image/scanned.

2. **The LLM Plugin:**
   - Implement the `OpenAIExtractor` plugin (implementing `IExtractionService`).
   - Setup Azure OpenAI (or standard OpenAI) API connections.

3. **Prompt Engineering & Security:**
   - Construct robust system prompts demanding JSON format output.
   - Implement Prompt Injection defenses using exact delimiter tags and rejection framing.
   - Implement the "Reflexion" mechanism (if Pydantic rejects the initial JSON, automatically retry the prompt once feeding the error back to the LLM).

4. **Testing:**
   - Write Contract Tests sending 5 varied, mock PDFs (or text blocks) to the actual OpenAI API to ensure it outputs the exact schema we require.

## ✅ Definition of Done
- The `OpenAIExtractor` successfully consumes messy text and returns an `LLMResponseBoundaryDTO`.
- Scanned (image-only) PDFs are successfully routed to the OCR fallback.
- Prompt injection attempts do not crash the system or pollute the database.
