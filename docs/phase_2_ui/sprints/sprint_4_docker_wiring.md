# Phase 2 - Sprint 4: Dockerization & Orchestration

**Goal:** Integrate the new UI seamlessly into the existing Docker Compose cluster.

## 🎯 Deliverables

1. **Streamlit Dockerfile Update:**
   - Ensure `streamlit` and `pandas` and `requests` are in the main `requirements.txt`.
   - Create a `Dockerfile.ui` if Streamlit requires different packaging, or reuse the base python template.

2. **Docker Compose (`docker-compose.yml`):**
   - Define a new `ui` service.
   - Map it to port `8501:8501`.
   - Make it depend on the `api` service.
   - **Configuration Injection:** Explicitly supply `- API_BASE_URL=http://api:8000` to the container environment block so the UI knows how to resolve the internal Docker network.

3. **Data Persistence Volumes:**
   - Update the Docker Compose file to mount a volume for `./bdis_prod.db:/app/bdis_prod.db`.
   - (Crucial so data isn't wiped out every time the user brings down the containers).

## ✅ Definition of Done
- Running `docker compose up --build` launches 4 services simultaneously (API, Worker, Redis, UI).
- The user can open their browser on localhost:8501 and successfully pull data from the `api` container asynchronously.
