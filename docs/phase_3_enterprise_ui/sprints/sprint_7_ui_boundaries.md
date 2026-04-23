# Sprint 7: High-Availability Boundaries

**Goal:** Bulletproof the Streamlit UI against Top-Down re-render loops and internal Message Broker crashes.

## 🎯 Deliverables

1. **State Management:** 
   - Identify the primary API Fetch layer inside `app.py`.
   - Enforce the Network Memoization Rule by wrapping the fetch function in `@st.cache_data(ttl=15)`.

2. **Graceful Degradation (Error Bound):**
   - Import the `ErrorViewModel` to intercept crashes triggered by Celery or FastAPI.
   - Stop UI Execution with an `if isinstance(data, ErrorViewModel):` check.
   - Render a polished, styled semantic warning card in place of the data grid.

## ✅ Definition of Done
- Pressing interactive buttons on the UI does not trigger redundant `GET /documents` API calls.
- If the Redis backend goes entirely offline, the UI does not print a python Traceback dump to the end-user.
