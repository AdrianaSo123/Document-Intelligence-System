# Sprint 1: The Core Domain & TDD Foundation

**Goal:** Establish the pure inner ring of the Clean Architecture. Build the business logic entirely isolated from any frameworks (no FastAPI, no Databases, no OpenAI). 

## 🎯 Deliverables

1. **Domain Entities:** 
   - Create the `DocumentInsight` pure Python dataclass.
   - Implement the `calculate_risk()` business logic.

2. **Abstract Interfaces (Ports):**
   - Define `IExtractionService` (Abstract Base Class).
   - Define `IDocumentRepository` (Abstract Base Class).

3. **Use Case Interactors:**
   - Implement `ProcessDocumentUseCase`.
   - Wire the Use Case to accept the Interfaces via Dependency Injection.

4. **Testing (TDD):**
   - Create `MockExtractionService` and `MockDocumentRepository`.
   - Write comprehensive Unit Tests verifying that if the mock extractor returns specific data, the Domain Entity correctly calculates risk and the Use Case calls `save_document()`.

## ✅ Definition of Done
- All core logic is implemented in simple Python files.
- Pytest suite runs in <100ms.
- 100% test coverage on the Domain and Use Case folders.
