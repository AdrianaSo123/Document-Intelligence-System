# Sprint 6C1: Durable Jobs + Worker Tenancy Propagation

**Goal:** Make the async pipeline enterprise-correct by persisting job state in the relational database and enforcing `workspace_id` through Celery task payloads and worker persistence.

## 🔗 Prerequisites / Dependencies

- Sprint 6B completed (RequestContext + membership enforcement exists so the API can safely enqueue workspace-scoped jobs).

## 🎯 Deliverables

1. **Jobs table (authoritative lifecycle):**
   - Add a `jobs` table with:
     - `job_id` (Celery task id)
     - `workspace_id`
     - `document_id`
     - `trace_id`
     - `status` (PENDING/PROCESSING/COMPLETE/FAILED)
     - timestamps + error fields

2. **Lifecycle updates (API + worker):**
   - API creates a DB job record at enqueue time (PENDING).
   - Worker updates the DB record:
     - PROCESSING on start
     - COMPLETE/FAILED on end

3. **Celery payload tenancy:**
   - Ensure Celery task payload includes `workspace_id` (non-optional).
   - Enforce conflict safety:
     - worker must not accept missing `workspace_id`

4. **Retry safety (at least once delivery):**
   - Persist extractions deterministically by `(workspace_id, document_id)` (upsert or reject—must be stable).

## ✅ Definition of Done

- Job state survives restarts because it is stored in the relational DB.
- Worker processing cannot write a record without a `workspace_id`.
- Tests prove:
  - a job in workspace A cannot be read/updated as workspace B
  - retrying a job does not create unbounded duplicate extraction rows

**Implemented (current reality):**
- Durable job rows are created at enqueue time and `GET /jobs/{job_id}` reads from the DB.
- Worker updates durable job status using the Celery task request id when available.
- Test coverage includes workspace-scoped job lookup in `tests/test_api/test_auth_context_rbac.py`.

