# Phase 2 - Sprint 2: The Streamlit Foundation & API Client

**Goal:** Establish the UI Data boundaries using the Humble Object Pattern, followed by the basic Streamlit application shell.

## 🎯 Deliverables

1. **View Models (`view_models.py`):**
   - Define a `DashboardViewModel` using Pydantic or native Python Dataclasses to represent the specific format the UI expects data to be in (e.g., enforcing string formatting or boolean mappings for risk).

2. **The API Client (`api_client.py`):**
   - Create a `BdisApiClient` class encapsulating the `requests` library.
   - Inject portability: Ensure the client reads `os.getenv("API_BASE_URL", "http://localhost:8000")` instead of hardcoding hostnames.
   - Implement methods: `upload_file()`, `get_status()`, and `fetch_all_documents()`.
   - **Crucial:** Catch `requests.ConnectionError` and return safe `Result` or `Optional` types.

3. **Application Shell (`app.py`):**
   - Initialize the Streamlit app.
   - Inject custom CSS enforcing dark mode and clean typography.
   - Inject the `BdisApiClient` into the view context.

4. **The Upload Component:**
   - Create a file uploader allowing `.pdf`.
   - On submit, call `api_client.upload_file()`.
   - Implement the visual status polling loop utilizing the client.

## ✅ Definition of Done
- A user can open `localhost:8501`, drop a PDF, and the UI successfully delegates to the API Client to trigger the backend without mixing logic.
- If the backend is intentionally turned off, the UI displays a clean "Service Unavailable" banner instead of an unhandled traceback.
