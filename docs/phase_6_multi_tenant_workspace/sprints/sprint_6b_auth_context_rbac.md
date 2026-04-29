# Sprint 6B: Auth Context + RBAC (Source of Truth Hardening)

**Goal:** Implement enterprise-grade request context resolution and RBAC enforcement so every API operation is both authenticated (authn) and authorized (authz) with workspace-scoped correctness.

## 🔗 Prerequisites / Dependencies

- Sprint 6A2 completed (repositories and ports are workspace-scoped).

## 🎯 Deliverables

1. **RequestContext boundary (Humble API):**
   - Introduce a `RequestContext` object containing:
     - `workspace_id`
     - `user_id`
     - `role`
     - `trace_id`
   - Ensure routers resolve `RequestContext` and pass it into use cases (no raw headers in use cases).

2. **Dev-only identity mode (safe and explicit):**
   - Implement `BDIS_AUTH_MODE=dev_headers` gated identity:
     - `X-BDIS-User-Id`
     - `X-BDIS-Workspace-Id`
     - `X-BDIS-Role`
   - In any non-dev mode, `X-BDIS-*` headers MUST be ignored (or rejected).

   **Implemented approach (current reality):**
   - Role is derived from `workspace_memberships` (DB source of truth).
   - `X-BDIS-Role` is optional; if present it must match the DB membership role.

3. **Workspace membership enforcement (anti-leak):**
   - Implement membership checks:
     - Route `workspace_id` MUST be in caller’s memberships.
   - Implement the **conflict rule**:
     - If identity-derived workspace (header/token claim) conflicts with route `workspace_id`, reject.

4. **RBAC enforcement (minimum viable):**
   - Enforce role requirements at the router boundary (or via dependency policy):
     - `OWNER`: workspace admin operations
     - `ANALYST`: upload/enqueue + reads
     - `AUDITOR`: read-only
   - Ensure auditors cannot upload or mutate state.

5. **Bootstrap workflow (no hidden magic):**
   - Add a safe bootstrap mechanism for dev mode (choose one):
     - a seed script in `scripts/`
     - an owner-only admin endpoint that creates workspace + membership
   - Avoid auto-creating privileged workspaces “on first request.”

6. **Audit events (foundation):**
   - Persist minimum audit events (workspace + membership + job enqueue):
     - `workspace.created`
     - `membership.added`
     - `job.enqueued`
   - Ensure audit metadata contains no raw document text and no PII.

   **Implemented approach (current reality):**
   - `audit_events` table created via Alembic migration.
   - API emits `job.enqueued` on successful enqueue (metadata includes filename only).
   - `audit_events.timestamp` is stored as a real DateTime (UTC).
   - SQLite hardening: migration defensively drops stale index names and relies on column-level indexes (prevents “index already exists” failures).

## ✅ Definition of Done

- Every API request resolves a `RequestContext` and enforces:
  - membership validation
  - RBAC rules
  - route/identity workspace conflict rejection
- In dev mode, a developer can bootstrap a workspace + membership and operate the system.
- In non-dev mode, `X-BDIS-*` headers cannot be used for privilege escalation.
- Tests prove:
  - a user in workspace A cannot read/write resources in workspace B
  - an auditor cannot upload or enqueue jobs

**Test coverage (implemented):**
- `tests/test_api/test_auth_context_rbac.py`

