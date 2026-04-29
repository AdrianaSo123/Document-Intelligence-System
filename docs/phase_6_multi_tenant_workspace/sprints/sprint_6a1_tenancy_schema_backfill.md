# Sprint 6A1: Tenancy Schema + Default Workspace Backfill

**Goal:** Introduce the minimum database structures required for multi-tenancy and safely migrate existing single-tenant data into a `Default Workspace`.

## 🔗 Prerequisites / Dependencies

- None (this is the first Phase 6 implementation sprint).

## 🎯 Deliverables

1. **Core tenancy tables:**
   - Add tables:
     - `workspaces`
     - `users`
     - `workspace_memberships`

2. **Workspace scoping columns:**
   - Add `workspace_id` to all tenancy-bearing tables:
     - `documents`
     - `extractions`
     - `evaluations`
     - `insights` (move from singleton to per-workspace)

3. **Migration strategy (enterprise hygiene):**
   - Introduce Alembic migrations (preferred enterprise path).
   - Add a “default workspace” backfill:
     - Create a `Default Workspace` with a deterministic ID for migration stability:
       - `workspace_id = "00000000-0000-0000-0000-000000000001"`
     - Backfill all existing rows into that workspace

   - Convert `insights` to per-workspace shape:
     - composite primary key: `(workspace_id, id)` (typically `id="current"`)
     - SQLite-safe rebuild strategy: `rename → create new → copy rows → drop old`

4. **Constraints (prevent future incidents):**
   - Add uniqueness constraints (or prepare for deterministic upserts) on:
     - `(workspace_id, document_id)` at minimum
   - Add indexes for:
     - `(workspace_id, document_id)`

## ✅ Definition of Done

- A fresh database can be migrated to the new schema (e.g., `alembic upgrade head`) without manual intervention.
- An existing database can be migrated without data loss, with all legacy data assigned to `Default Workspace`.
- `insights` are workspace-scoped (no singleton assumption remains) using `(workspace_id, id)` composite key.
- Tests prove:
  - the migration/backfill result matches expected row counts and workspace assignment
  - new rows cannot be created without `workspace_id` where required (or the application layer supplies it deterministically)

