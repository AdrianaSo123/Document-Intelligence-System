# Sprint 6A2: Tenancy Ports + Repository Refactor (Anti-Leak Enforcement)

**Goal:** Make tenancy enforcement non-optional by pushing `workspace_id` through Ports and ensuring all repository operations are workspace-scoped.

## 🔗 Prerequisites / Dependencies

- Sprint 6A1 completed (schema includes `workspace_id` columns and workspace tables).

## 🎯 Deliverables

1. **Port refactor (tenancy becomes a required input):**
   - Update `IDocumentRepository` so every method requires `workspace_id`, including:
     - `save(workspace_id, extraction)`
     - `get_all(workspace_id)`
     - `get_by_document_id(workspace_id, document_id)` (or equivalent)
   - Update any other ports that currently read/write tenant data to accept `workspace_id` (jobs, audit events, insights).

2. **Adapter refactor (SQLAlchemy repository):**
   - Scope every query by `workspace_id`.
   - Ensure persistence includes `workspace_id` on all inserted/updated rows.

   - Fix legacy uniqueness constraints:
     - Remove global uniqueness on `documents.document_id`
     - Replace with workspace-scoped uniqueness: `(workspace_id, document_id)`

   - Enforce tenant-safe referential integrity:
     - Use composite FK constraints from `extractions/evaluations` → `documents` on `(workspace_id, document_id)`

3. **Duplication control (retry safety):**
   - Define one deterministic policy (pick one and enforce):
     - **Upsert** the `documents` row by `(workspace_id, document_id)` (recommended), or
     - **Reject duplicates** with a clear error and stable job semantics

   **Implemented approach (current reality):**
   - `documents`: upsert-style behavior (re-use existing `(workspace_id, document_id)` row)
   - `extractions`: append-only history (new row per run) while remaining workspace-scoped

4. **Unit tests (prove the invariant):**
   - Repository “anti-leak” tests:
     - workspace A cannot read workspace B rows via any method
   - Collision tests:
     - same `document_id` in two workspaces does not collide

## ✅ Definition of Done

- It is impossible to call repository reads/writes without supplying `workspace_id`.
- All SQL queries include a workspace filter (or equivalent scoping mechanism).
- Tests prove:
  - the anti-leak invariant at the repository layer
  - same `document_id` can exist in multiple workspaces without collision
  - duplicate handling policy is deterministic (upsert or reject) under retries

