# Phase 2 - Sprint 1: Backend API Expansion

**Goal:** Provide the necessary HTTP data endpoints so the new UI can fetch historical data without touching the database directly.

## 🎯 Deliverables

1. **Repository Enhancement:**
   - Add a `get_all()` method to the abstract `IDocumentRepository`.
   - Implement `get_all()` inside `SqliteDocumentRepository` to return a list of `DocumentInsightModel` records.

2. **API Endpoint Construction:**
   - Open `src/bdis/frameworks/api/main.py`.
   - Create a `GET /documents` endpoint.
   - Use Dependency Injection to acquire the repository and fetch the data.

## ✅ Definition of Done
- A `curl` request to `GET /documents` successfully returns a JSON array of parsed data entities.
- Validated via automated integration testing.
