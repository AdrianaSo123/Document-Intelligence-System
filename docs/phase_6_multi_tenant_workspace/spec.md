# 🏢 PHASE 6 MASTER SPEC: Multi-Tenant Workspace Architecture (Enterprise SSO + RBAC)

---

## 0. Executive framing

Phase 6 transforms BDIS from a single-tenant demo into a **multi-tenant enterprise platform**. The system will support multiple organizations (“Workspaces”), multiple users per workspace, and strict data isolation guarantees enforced across:

- **API authorization**
- **database queries**
- **object storage paths (S3/MinIO)**
- **async jobs (Celery)**
- **audit trails**

This phase is explicitly designed to signal **FDE readiness**: security-by-default, clean boundary design, safe migration strategy, and production-operable identity/tenancy patterns.

---

## 1. 🎯 Objective & business value

### 1.1 Objective

Introduce a first-class **Workspace** concept and enforce per-workspace isolation end-to-end while preserving Clean Architecture boundaries.

### 1.2 Why this matters (enterprise reality)

In enterprise environments, the same application must be safely shared by multiple teams, departments, or customers. Multi-tenancy is where “toy systems” usually fail due to:

- authorization gaps (“horizontal privilege escalation”)
- accidental data leakage in background jobs
- missing auditability and traceability

Phase 6 makes BDIS defensible under a real security review.

---

## 2. 🧠 Core philosophy (non-negotiable rules)

### 2.1 Tenancy is a *policy*, not a feature toggle

- **Rule:** Tenancy must be modeled explicitly in the Domain and propagated as a first-class value through Use Cases.
- **Rule:** Every persistence operation MUST scope by `workspace_id`.
- **Rule:** Every file stored in object storage MUST be partitioned by `workspace_id`.
- **Rule:** Every Celery job MUST carry `workspace_id` and MUST enforce it during processing and persistence.

### 2.2 The Dependency Rule (Clean Architecture preserved)

- FastAPI/Streamlit are *outer layers*. Identity/authorization parsing may live there, but **policy enforcement must be expressed in Use Cases** and/or Ports.
- Repository implementations may use SQLAlchemy, but MUST NOT be able to query cross-tenant data without receiving explicit `workspace_id`.

### 2.3 Least privilege by default

- Anonymous access is forbidden in multi-tenant mode.
- “Allow all origins” CORS is forbidden outside local dev.
- Every endpoint must have a clear **authn + authz** policy.

---

## 3. 🧱 Domain model (new enterprise primitives)

### 3.1 New domain entities / value objects

#### 3.1.1 `WorkspaceId` (Value Object)

- A typed wrapper around UUID strings.
- Prevents accidental mixing with `document_id` / `trace_id`.

#### 3.1.2 `Workspace`

Represents an organization boundary.

Minimum attributes:
- `workspace_id`
- `name`
- `created_at`
- `status` (ACTIVE / SUSPENDED)

#### 3.1.3 `User`

Represents an identity in the system (mapped from auth provider).

Minimum attributes:
- `user_id` (provider subject / UUID)
- `email`
- `display_name`

#### 3.1.4 `WorkspaceMembership`

Join entity mapping Users to Workspaces.

Minimum attributes:
- `workspace_id`
- `user_id`
- `role` (see RBAC)
- `created_at`

#### 3.1.5 `Role` (RBAC enum)

Enterprise-grade, minimal surface area:
- `OWNER`: workspace administration, billing-style settings, user management
- `ANALYST`: can upload/process documents, view results
- `AUDITOR`: read-only; can view documents + audit logs

---

## 4. 🛡️ Authorization model (RBAC + policy)

### 4.1 Authentication strategies (two modes)

BDIS will support two identity modes to keep the project runnable while still enterprise-shaped.

#### Mode A (Local Dev): Header-based identity (explicitly dev-only)

- `X-BDIS-User-Id`
- `X-BDIS-Workspace-Id`
- `X-BDIS-Role`

This mode exists to keep the portfolio demo self-contained without requiring a full IdP setup.

**Hard boundary (dev-only):**
- Dev header auth MUST be gated behind an explicit configuration flag (e.g., `BDIS_AUTH_MODE=dev_headers`).
- In any non-dev mode, requests containing `X-BDIS-*` identity headers MUST be ignored (or rejected) to prevent privilege injection.

**Implemented in Sprint 6B (current reality):**
- `BDIS_AUTH_MODE=dev_headers` enables `X-BDIS-User-Id` + `X-BDIS-Workspace-Id`.
- `X-BDIS-Role` is optional; if provided it must match DB membership (role is derived from `workspace_memberships`).

#### Mode B (Enterprise): OIDC (Cognito / Auth0 / Okta compatible)

- Access token contains:
  - `sub` (user id)
  - `email`
  - `workspace_id` (or organization claim)
  - `roles` (or group membership)

**Note:** The infrastructure file `infrastructure/aws_ecs_deployment.yml` already frames Cognito at the edge. Phase 6 makes the application layer actually compatible with that plan.

**Implemented (Phase 6 completion):**
- `BDIS_AUTH_MODE=oidc` supports Bearer JWT authentication.
- Offline/test support uses `OIDC_JWT_ALG=HS256` + `OIDC_JWT_SECRET`.
- Production-intended mode uses `OIDC_JWT_ALG=RS256` + `OIDC_JWKS_URL` (JWKS key fetch + signature verification).

### 4.2 Authorization policy (required checks)

Every request must be evaluated against:

- **Workspace scope**: request is bound to exactly one `workspace_id`.
- **Role**: endpoint declares minimum required role(s).
- **Object ownership**: document/job must belong to the caller’s workspace.

**Enterprise-grade source-of-truth rules:**
- The authoritative `workspace_id` for data access MUST come from the request route (e.g., `/workspaces/{workspace_id}/...`), not from a mutable client-provided header.
- The caller’s role MUST be derived from a trusted source:
  - OIDC claims/groups in Mode B, or
  - `workspace_memberships` in the relational database (recommended once available).
- A request MUST be rejected if the route `workspace_id` is not in the caller’s workspace memberships.

### 4.3 Anti-leak invariant (the one-liner)

> A user must never be able to read/write any resource whose `workspace_id` is not equal to their current workspace.

This invariant must be test-covered at the API and repository boundaries.

---

## 5. 🗄️ Persistence design (schema + isolation)

### 5.1 Database migration strategy (mandatory)

The current approach uses `Base.metadata.create_all()`. That is acceptable for early phases, but Phase 6 requires:

- **Alembic migrations** for schema evolution
- idempotent upgrades
- a clean story for “existing single-tenant data” migration

**Implementation note (Phase 5 not required):**
- Phase 6 can be implemented on **SQLite** (local/dev) or **Postgres** (recommended for production).
- The multi-tenant model must be **database-agnostic**. Postgres improves concurrency and ops, but tenancy correctness must not depend on it.

### 5.2 Schema changes (database-agnostic)

#### 5.2.1 Tenancy columns

Add `workspace_id` to all tenancy-bearing tables:

- `documents.workspace_id`
- `extractions.workspace_id`
- `evaluations.workspace_id`
- `jobs.workspace_id` (new table in this phase; see below)
- `insights.workspace_id` (move from singleton to per-workspace)

**Implemented in Sprint 6A1 (current reality):**
- `insights` is now keyed by a composite primary key: `(workspace_id, id)` where `id` is typically `"current"`.
- For SQLite compatibility, converting `insights` from the old singleton shape requires a safe table rebuild (`rename → create new → copy rows → drop old`).

#### 5.2.2 New tables

- `workspaces`
- `users`
- `workspace_memberships`
- `audit_events`
- `jobs` (durable job tracking; do not rely solely on Celery backend state)

### 5.3 Indexing & constraints (enterprise-grade defaults)

- Composite index: `(workspace_id, document_id)` for all primary reads
- Unique constraint: `(workspace_id, document_id)` to prevent duplicates on retries
- Foreign keys always include `workspace_id` boundaries where applicable

**Migration note (implemented vs. planned):**
- Sprint 6A1 adds `workspace_id` and backfills legacy rows.
- If the legacy schema has a global uniqueness constraint on `documents.document_id` (it currently does), that constraint must be removed in Sprint 6A2 and replaced with a workspace-scoped uniqueness policy (e.g., unique on `(workspace_id, document_id)`).

### 5.4 Repository contracts (ports must change)

The `IDocumentRepository` port must become tenancy-aware.

- **Rule:** Every method MUST accept `workspace_id`.
- **Rule:** No method may return “all documents” without a `workspace_id`.

Example (conceptual):

- `save(workspace_id, extraction)`
- `get_all(workspace_id)`
- `get_by_document_id(workspace_id, document_id)`

---

## 6. 📦 Object storage partitioning (S3/MinIO)

### 6.1 Keyspace design

All archived files must live under:

`s3://<bucket>/workspaces/<workspace_id>/documents/<document_id>/<original_filename>`

**Implementation note (Phase 5 not required):**
- If S3/MinIO is not implemented, the system may use a `LocalFileStorageAdapter` that writes to:
  - `storage/workspaces/<workspace_id>/documents/<document_id>/<original_filename>`
- The path scheme MUST remain identical between local and cloud modes to preserve deployment parity.

### 6.2 Storage Port upgrade

`IFileStorage.upload_file(...)` must accept:

- `workspace_id`
- `document_id`
- `filename`

**Implemented (Phase 6 completion):**
- Storage uploads are partitioned by workspace/document:
  - `workspaces/<workspace_id>/documents/<document_id>/...`
- Local fallback uses:
  - `storage/workspaces/<workspace_id>/documents/<document_id>/...`

### 6.3 Security note

Even on MinIO in local dev, we keep the path scheme identical. This keeps cloud deployment friction near-zero.

---

## 7. ⚙️ Job orchestration (Celery) with tenancy correctness

### 7.1 Why Celery status is not enough

Celery’s backend status is a convenience, not an enterprise audit log. Phase 6 requires a **durable Job record** stored in the primary relational database (SQLite for dev, Postgres recommended for production) with:

- `job_id` (celery id)
- `workspace_id`
- `document_id`
- `trace_id`
- `status` (PENDING/PROCESSING/COMPLETE/FAILED)
- timestamps (created/updated)
- error fields

### 7.2 Job lifecycle (authoritative source)

The authoritative job status must come from the `jobs` table, updated by:

- the API at enqueue time (PENDING)
- the worker at start (PROCESSING)
- the worker at end (COMPLETE/FAILED)

This ensures:

- debuggability when Celery backend is reset
- a stable history for audit and compliance
- a clean UI experience (“jobs list”) without coupling to Celery internals

**Implemented in Sprint 6C1 (current reality):**
- A durable `jobs` table exists (Alembic migration) with:
  - `job_id`, `workspace_id`, `document_id`, `trace_id`, `status`, timestamps, `error_message`
- `GET /jobs/{job_id}` is workspace-scoped via `RequestContext` and reads from the relational DB (not Celery backend).
- The worker updates job status on a best-effort basis (PROCESSING/COMPLETE); failures to update status do not crash the worker.
 - Worker updates FAILED status + `error_message` on exceptions and emits `job.completed` / `job.failed` audit events (best-effort).

### 7.3 Idempotency & retry safety

Workers and repositories must be safe under “at least once” delivery:

- **Rule:** `document_id` is generated by the API and passed through the entire system.
- **Rule:** DB writes MUST be deterministic under retries.
  - Recommended: **upsert** the `documents` identity row by `(workspace_id, document_id)` and treat `extractions` as append-only history.
  - Alternatively: reject duplicates deterministically with a stable error and job semantics.
- **Rule:** If a job is retried, the system must update the existing extraction record rather than creating an unbounded stream of duplicates.

**Implementation note (current approach through Sprint 6A2):**
- The system keeps an append-only extraction history (multiple `extractions` rows per `(workspace_id, document_id)` are allowed).
- “Unbounded duplicates” will be addressed at the Job layer in Sprint 6C1 by linking jobs ↔ extractions and enforcing stable job semantics.

---

## 8. 🔌 API design (tenancy-aware contracts)

### 8.1 API versioning

Phase 6 introduces breaking changes in contracts (workspace-scoped reads). Therefore:

- New endpoints are introduced under `/v1/*` (recommended), or
- Existing endpoints remain but become tenancy-aware and require auth headers.

### 8.2 Required request context

Every request must resolve a `RequestContext`:

- `workspace_id`
- `user_id`
- `role`
- `trace_id` (generated per request if missing)

This object is passed to Use Cases (never raw header strings).

**Conflict rule (anti-confusion / anti-leak):**
- If a request supplies any identity-derived `workspace_id` (dev headers or token claim) and it does not match the route `workspace_id`, the request MUST be rejected.

### 8.3 Endpoints (minimum set)

#### Workspaces

- `POST /workspaces` (OWNER only) — create a workspace
- `GET /workspaces/me` — list workspaces user belongs to (or return current)
- `POST /workspaces/{workspace_id}/members` (OWNER only) — invite/add member
- `GET /workspaces/{workspace_id}/members` (OWNER/AUDITOR) — list members

#### Documents & jobs (workspace-scoped)

- `POST /workspaces/{workspace_id}/jobs` — upload + enqueue
- `GET /workspaces/{workspace_id}/jobs/{job_id}` — job status (from DB, not Celery)
- `GET /workspaces/{workspace_id}/documents` — documents in this workspace only
- `GET /workspaces/{workspace_id}/insights` — insights for this workspace only

**Implemented in Sprint 6C2 (current reality):**
- Workspace-prefixed routes exist and enforce route scoping:
  - route `{workspace_id}` MUST equal `RequestContext.workspace_id` or the request is rejected.
- Compatibility aliases remain:
  - `GET /documents` and `GET /insights` are still available (workspace-scoped via `RequestContext`).
  - `GET /jobs/{job_id}` remains DB-backed and workspace-scoped via `RequestContext`.

**Lookup hardening rules:**
- All read endpoints MUST scope lookups by `(workspace_id, <resource_id>)` (e.g., `(workspace_id, job_id)` and `(workspace_id, document_id)`).
- The API MUST never return a resource by `job_id` or `document_id` without also verifying the `workspace_id` match (prevents ID guessing / horizontal escalation).

### 8.4 Authorization matrix (RBAC)

- `OWNER`
  - manage workspace + memberships
  - view audit events
  - full access to documents/jobs/insights
- `ANALYST`
  - upload/enqueue jobs
  - view documents/jobs/insights
- `AUDITOR`
  - view documents/jobs/insights (read-only)
  - view audit events (read-only)

---

## 9. 🖥️ UI updates (workspace-aware enterprise console)

### 9.1 Workspace selector (sidebar)

The Streamlit UI must:

- display the current workspace
- allow switching between workspaces the user belongs to
- never show cross-workspace documents in a single table

**Implemented in Sprint 6C2 (current reality):**
- UI calls `GET /workspaces/me` to populate a workspace selector.
- UI uses workspace-prefixed routes for documents/jobs and switches the header context when the user changes workspace.

### 9.2 Membership-aware features

- Owners get a “Workspace Admin” panel:
  - member list
  - add member
  - role changes (optional)
- Auditors do not see upload controls.

### 9.3 Local dev usability

In dev mode, the UI can set workspace/user via environment variables and pass them as headers through `BdisApiClient`.

**Bootstrap rule (no hidden magic):**
- The dev workflow MUST include an explicit bootstrap step to create a workspace + membership (seed script or admin endpoint), rather than silently auto-creating privileged workspaces on first request.

---

## 10. 🧾 Audit logging (enterprise requirement)

### 10.1 What is audited

Minimum audit events:

- `workspace.created`
- `membership.added`
- `document.uploaded`
- `job.enqueued`
- `job.completed`
- `job.failed`
- `document.viewed` (optional; only if needed for “who accessed what”)

### 10.2 Audit event schema

Every event must include:

- `event_id`
- `workspace_id`
- `actor_user_id`
- `event_type`
- `resource_type` + `resource_id` (optional)
- `trace_id`
- `timestamp`
- `metadata_json` (strictly non-PII)

**Implemented in Sprint 6B (current reality):**
- `audit_events` table exists via Alembic migration.
- API writes `job.enqueued` on successful enqueue with non-PII metadata (e.g., filename).

**Implemented (Phase 6 completion):**
- Additional audit events are emitted where applicable:
  - `document.uploaded` (API)
  - `job.completed` / `job.failed` (worker best-effort)

### 10.3 Privacy rule

- **Rule:** Audit logs must never store raw document text.
- **Rule:** Audit logs must never store extracted PII.

---

## 11. 🔭 Observability & traceability upgrades

### 11.1 Structured logs include tenancy

Every log line in the request/job lifecycle must carry:

- `trace_id`
- `workspace_id`
- `document_id` (when applicable)
- `job_id` (when applicable)

### 11.2 Correlation across services

API generates/propagates `trace_id` into:

- DB job record
- Celery task payload
- worker logs

---

## 12. 🧪 Testing strategy (prove isolation)

### 12.1 Unit tests (domain/use cases)

- Role policy tests (who can do what)
- RequestContext parsing tests
- “anti-leak” tests: repository never returns records for the wrong `workspace_id`

### 12.2 Integration tests (API + DB)

Run against the project’s configured relational database (SQLite in dev is acceptable; Postgres recommended) and assert:

- user A in workspace A cannot fetch documents for workspace B
- same `document_id` in two workspaces does not collide
- job status comes from DB and is workspace-scoped

### 12.3 Security regression tests

- upload endpoint rejects missing workspace/user context in non-dev mode
- auditor role cannot upload

---

## 13. 🚀 Migration & rollout plan (safe evolution)

### 13.1 Backfill strategy for existing single-tenant data

Create a default workspace:

- `workspace_id = "00000000-0000-0000-0000-000000000001"` (deterministic constant for migration stability)
- `name = "Default Workspace"`

Then backfill:

- all existing documents/extractions/evaluations/insights → that workspace

### 13.2 Incremental rollout

- Phase 6 can ship with Mode A (dev headers) enabled by default.
- Mode B (OIDC) can be added behind a config flag without schema changes.

---

## 14. ✅ Acceptance criteria (enterprise standard)

The phase is complete when:

- **Tenancy enforcement:** Every persisted record and query path is scoped by `workspace_id`.
- **Authorization correctness:** RBAC is enforced on all endpoints; auditors cannot mutate state.
- **Storage isolation:** Archived document storage paths (S3/MinIO or local filesystem adapter) are partitioned by `workspace_id` and `document_id`.
- **Job durability:** Job status is tracked in the relational database; UI does not rely on Celery backend state.
- **Auditability:** High-value events are persisted to `audit_events` without storing raw document text.
- **Tests:** Automated tests prove “no cross-tenant access” for API + repository paths.

---

## 16. ✅ Implementation status (Phase 6)

- [x] Tenancy schema + Default Workspace backfill (6A1)
- [x] Workspace-scoped repositories + constraints (6A2)
- [x] Dev-header auth mode + membership enforcement + RBAC (6B)
- [x] Audit events table + baseline events
- [x] Durable jobs table + DB-authoritative status (6C1)
- [x] Workspace-prefixed canonical routes + strict route scoping (6C2)
- [x] Storage partitioning by workspace/document (S3 keyspace + local fallback)
- [x] Optional OIDC auth mode (`BDIS_AUTH_MODE=oidc`)
- [x] UI workspace selector + jobs ledger + minimal owner admin panel

---

## 15. 📅 Sprint breakdown (recommended)

### Sprint 6A1: Tenancy schema + default workspace backfill

- Add Alembic + initial migrations
- Add `workspaces`, `users`, `workspace_memberships`
- Add `workspace_id` columns to existing tables + backfill Default Workspace
- Convert `insights` to per-workspace composite key `(workspace_id, id)`

**Definition of Done**
- `alembic upgrade head` works on SQLite
- Legacy data is safely backfilled to Default Workspace

### Sprint 6A2: Tenancy ports + repository enforcement

- Update Ports/use cases to require `workspace_id`
- Enforce workspace-scoped persistence and reads in repositories
- Replace global `documents.document_id` uniqueness with `unique(workspace_id, document_id)`
- Introduce composite FK constraints for tenant-safe referential integrity

**Definition of Done**
- Same `document_id` can exist in multiple workspaces without collision
- Repository reads cannot leak data across workspaces (tests)

### Sprint 6B: Auth context + RBAC

- Implement `RequestContext` + dev header auth mode
- Add RBAC enforcement at router/use case boundary
- Add audit event persistence for uploads/jobs

**Definition of Done**
- Two workspaces with same document IDs cannot access each other’s data
- Auditors are read-only across the system

### Sprint 6C1: Durable jobs + worker tenancy propagation

- Add `jobs` table and lifecycle updates (PENDING → PROCESSING → COMPLETE/FAILED)
- Ensure Celery payload carries `workspace_id` and worker persistence is tenant-scoped

**Definition of Done**
- Job status is stable via DB and workspace-scoped

### Sprint 6C2: Workspace-scoped endpoints + workspace-aware UI

- Implement workspace-scoped endpoints for jobs/documents/insights
- Add workspace selector + role-aware UI controls

**Definition of Done**
- UI can switch workspaces and shows isolated registries + insights

### (Deprecated) Sprint 6C: Workspace-aware UI + job durability

- Add workspace selector + owner/admin panel (minimal)
- Add `jobs` table and lifecycle updates (PENDING → PROCESSING → COMPLETE/FAILED)
- UI reads job status from API backed by DB

**Definition of Done**
- UI can switch workspaces and shows isolated registries + insights
- Job history is visible and stable across restarts

