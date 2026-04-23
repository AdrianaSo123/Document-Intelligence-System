# Phase 2 - Sprint 3: The Data Visualization Dashboard

**Goal:** Transform the strictly-typed View Models into an actionable, beautiful analytics display without causing severe API strain.

## 🎯 Deliverables

1. **Plumbing the Humble View & Caching:**
   - Call `api_client.fetch_all_documents()` to retrieve a list of strictly-typed `DashboardViewModel` objects.
   - **Crucial (Anti-DDoS):** You MUST wrap the fetch call in a function decorated with `@st.cache_data(ttl=30)` or store the fetch result in `st.session_state`. If you do not do this, every single interface click will hit the database!

2. **KPI Metric Cards:**
   - Render columns at the top of the UI.
   - Calculate Total Value and High Risk counts entirely off the properties defined exclusively in the View Models.

3. **Risk Highlighting Table:**
   - Convert the List of `DashboardViewModel`s into a Pandas DataFrame purely for the final `st.dataframe` rendering step.
   - Apply Pandas styling logic to highlight rows based on the boolean flags existing in the View Models.

## ✅ Definition of Done
- The app displays a beautiful, dynamic layout summarizing the extracted financial insights.
- Clicking around the table filters does not trigger a brand new backend log request (verifying the Cache rules are working).
