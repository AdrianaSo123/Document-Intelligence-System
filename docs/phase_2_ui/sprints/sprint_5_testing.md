# Phase 2 - Sprint 5: UI Testing & Verification

**Goal:** Prove the value of the Humble Object Pattern by writing unit tests for the UI that execute without actually spinning up Streamlit or connecting to the live API.

## 🎯 Deliverables

1. **API Client Unit Tests:**
   - Write a `pytest` test targeting `src/bdis/frameworks/ui/api_client.py`.
   - Deeply mock the `requests.get()` call using a library like `responses` or standard `Mock`.
   - Assert that if the mock returns a messy JSON packet with missing fields, the API Client successfully parses it and degrades gracefully to a valid Pydantic `DashboardViewModel`.

2. **Network Partition Tests:**
   - Mock a `requests.ConnectionError` and verify the `ApiClient` returns a clean None/Error Type rather than crashing.

3. **Metrics Logic Verification:**
   - Import the View Models and test that KPI calculations (e.g., grouping high-risk flags) work purely in memory using fake DTO objects.

## ✅ Definition of Done
- The `tests/test_ui/` directory executes rapidly alongside the Backend tests.
- UI tests are proven to be physically incapable of making real network calls (via strict mocking).
