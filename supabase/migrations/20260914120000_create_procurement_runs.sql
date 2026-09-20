-- Phase 8B -- procurement_runs table for Supabase PostgreSQL.
--
-- Authoritative source: reports/phase8a_supabase_multiuser_architecture.md
-- (Section 6) and reports/phase8a_architecture_decision_record.md
-- (ADR-6, ADR-8). This migration creates the table only -- it does not
-- touch, drop, or modify any other object in the target database.
--
-- SCOPE BOUNDARY (Phase 8B, read before applying):
--   - This migration is SCHEMA + RLS PREPARATION, not a claim that
--     multi-user security is complete. Authentication does not exist
--     anywhere in this project yet (explicitly out of Phase 8B's scope).
--   - The RLS policies below reference auth.uid() (Supabase's own
--     trusted, JWT-verified session function) -- never a client-supplied
--     value -- so they are safe and correct to define now, even though
--     no real authenticated request has ever exercised them yet. They
--     will not admit any anon/authenticated-role access until a real
--     session exists; the application backend (FastAPI) currently
--     connects with its own privileged, RLS-bypassing connection and
--     does not populate user_id at all (see
--     backend/persistence/supabase_repository.py's module docstring).
--   - End-to-end verification of these policies against real users is
--     explicitly deferred to a later phase (reports/phase8a_migration_roadmap.md,
--     Phase 8G), not claimed complete here.
--
-- This migration is idempotent (IF NOT EXISTS / safe re-run) and
-- contains no destructive statement (no DROP, no DELETE, no TRUNCATE).

create table if not exists procurement_runs (
    run_id                 uuid primary key default gen_random_uuid(),
    user_id                uuid references auth.users(id) on delete cascade,
    created_at             timestamptz not null default now(),
    commodity              text not null,
    run_status             text not null,
    eligible_vendor_count  integer not null,
    candidate_group_count  integer not null,
    selected_group_count   integer not null,
    input_json             jsonb not null,
    result_json            jsonb not null
);

-- Matches sqlite_repository.py's/supabase_repository.py's existing query
-- pattern exactly: "list a user's runs, newest first"
-- (ORDER BY created_at DESC, run_id DESC).
create index if not exists idx_procurement_runs_user_created
    on procurement_runs (user_id, created_at desc);

-- --------------------------------------------------------------------
-- Row Level Security -- PREPARED, not yet exercised by any real
-- authenticated request (see scope boundary above).
-- --------------------------------------------------------------------

alter table procurement_runs enable row level security;

-- SELECT / INSERT only: these are the only two operations any existing
-- code path performs (backend/persistence/repository.py's interface has
-- no update/delete method, matching the immutable-snapshot design
-- Phase 6G already established). No UPDATE or DELETE policy exists,
-- because no such policy is needed by anything in this project today
-- (ADR-6) -- inventing one now would be speculative, unrequested CRUD.

create policy "procurement_runs_select_own"
    on procurement_runs
    for select
    using (auth.uid() = user_id);

create policy "procurement_runs_insert_own"
    on procurement_runs
    for insert
    with check (auth.uid() = user_id);

-- NOTE: user_id currently allows NULL (no NOT NULL constraint) because
-- Phase 8B's own persistence code never writes it -- there is no
-- verified identity to populate it with yet (authentication is a later
-- phase). A future migration, applied alongside the phase that
-- introduces authentication, should both (a) backfill or otherwise
-- resolve any existing NULL rows and (b) add `not null` to this column
-- once every write path can supply a real, verified user_id. Adding
-- `not null` now would make this table unusable by Phase 8B's own
-- (auth-free) persistence code.
