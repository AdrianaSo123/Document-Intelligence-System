# Sprint 8: The PostgreSQL Transition

**Goal:** Eradicate all `sqlite3` persistence mappings. Spin up a true ACID-compliant relational database cluster and rewire the FastAPI and Celery services to authenticate against it natively.

## 🎯 Deliverables

1. **Service Orchestration (`docker-compose.yml`):** 
   - Inject the `postgres:15` image.
   - Define secure local environment variables (`POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`).
   - Assign a persistent `postgres_data` volume.

2. **Adapter Refactoring:**
   - Add `psycopg2-binary` to the global `requirements.txt`.
   - Ensure `dependencies.py` correctly pulls the dynamic `DATABASE_URL` format.

## ✅ Definition of Done
- Connecting to `bdis_prod.db` is officially impossible.
- Docker seamlessly builds a dedicated `postgres` container upon launch.
