# Sprint 6C2: Workspace-Scoped Endpoints + Workspace-Aware UI

**Goal:** Deliver the visible enterprise feature: workspace-scoped endpoints and a UI that can switch workspaces without any cross-tenant mixing, while enforcing lookup hardening (no ID guessing leaks).

## 🔗 Prerequisites / Dependencies

- Sprint 6C1 completed (jobs are durable and worker tenancy propagation is enforced).

## 🎯 Deliverables

1. **Workspace-scoped endpoints (ready for UI):**
   **Context (what Sprint 6C1 shipped):**
   - Durable job lifecycle is already DB-backed and workspace-scoped via `RequestContext` at:
     - `POST /jobs/create`
     - `GET /jobs/{job_id}` (from DB)

   **Sprint 6C2 target (canonical enterprise API shape):**
   - Add canonical workspace-prefixed routes:
     - `POST /workspaces/{workspace_id}/jobs`
     - `GET /workspaces/{workspace_id}/jobs/{job_id}` (from DB, not Celery backend)
     - `GET /workspaces/{workspace_id}/documents`
     - `GET /workspaces/{workspace_id}/insights`

   **Backward compatibility (recommended):**
   - Keep existing non-prefixed routes as compatibility aliases for the UI while transitioning:
     - `POST /jobs/create` → routes to the same implementation
     - `GET /jobs/{job_id}` → routes to the same implementation
   - Both route shapes MUST enforce that route `{workspace_id}` (when present) matches `RequestContext.workspace_id`.

2. **Lookup hardening (horizontal escalation prevention):**
   - All reads MUST be scoped by `(workspace_id, id)`:
     - `(workspace_id, job_id)`
     - `(workspace_id, document_id)`
   - Never return a resource by ID without verifying workspace match.

3. **Streamlit workspace selector + role-aware UI:**
   - Add workspace selector in the sidebar.
   - Owners see “Workspace Admin” panel (members list + add member).
   - Auditors do not see upload/enqueue controls.
   - UI never renders mixed-workspace tables.

4. **Jobs ledger UX:**
   - UI displays job list/status from API backed by DB.
   - UI polling (if any) uses job endpoints, not Celery internals.

## ✅ Definition of Done

- Switching workspaces changes the entire registry/insights/jobs ledger view without mixing records.
- An auditor role cannot upload or enqueue via the UI.
- Tests prove ID guessing is prevented:
  - `job_id` from workspace A cannot be fetched through workspace B routes.

- Tests prove route-scoping correctness:
  - calling `/workspaces/{workspace_id}/jobs/{job_id}` with a mismatched `RequestContext.workspace_id` is rejected.

**Implemented (current reality):**
- Workspace-prefixed routes are live for jobs/documents/insights.
- UI uses `GET /workspaces/me` to populate the workspace selector.
- Test coverage includes:
  - `tests/test_api/test_auth_context_rbac.py::test_workspace_prefixed_job_route_rejects_mismatch`

