# Sprint 2: Interface Adapters & Database

**Goal:** Connect the core logic to real-world boundary objects and persistent storage, while strictly respecting the Dependency Rule.

## 🎯 Deliverables

1. **Boundary DTOs:**
   - Create `LLMResponseBoundaryDTO` using Pydantic.
   - Enforce strict typing (ISO 8601 for dates, ISO 4217 for currencies).

2. **Database Schema & Implementation:**
   - Set up SQLite architecture.
   - Implement the `SqliteDocumentRepository` plugin (which implements the `IDocumentRepository` interface).
   - Write ORM mapping (if using SQLAlchemy or SQLModel) to convert from the pure `DocumentInsight` Entity to the Database row.

3. **Validation Error Handling:**
   - Ensure mapping failures from dirty dictionaries to the boundary DTO raise actionable validation errors.

4. **Testing:**
   - Write Integration Tests for `SqliteDocumentRepository`.
   - Setup a temporary test database during pytest execution to verify insert/read behaviors.

## ✅ Definition of Done
- Database tables are successfully generating.
- Documents can be saved and retrieved via the Repository layer.
- Invalid data is aggressively rejected by Pydantic before it can even reach the Use Case.
