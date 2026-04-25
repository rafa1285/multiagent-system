-- Observability trace schema (UP migration)
-- Date: 2026-04-25

create extension if not exists pgcrypto;

create schema if not exists observability;

create table if not exists observability.app_runs (
  run_id uuid primary key,
  user_id uuid,
  user_ref_hash text,
  operation_kind text not null check (operation_kind in ('create', 'modify', 'delete')),
  source_channel text not null check (source_channel in ('whatsapp', 'webhook', 'manual')),
  source_message_id text,
  n8n_execution_id text,
  app_id text,
  requested_at timestamptz not null default now(),
  completed_at timestamptz,
  final_status text not null default 'running'
    check (final_status in ('running', 'success', 'failed', 'cancelled')),
  production_url text,
  jira_parent_issue_key text,
  github_repo text,
  github_default_branch text,
  metadata jsonb not null default '{}'::jsonb
);

create table if not exists observability.app_trace_events (
  event_id uuid primary key default gen_random_uuid(),
  run_id uuid not null references observability.app_runs(run_id) on delete cascade,
  occurred_at timestamptz not null default now(),

  -- Step/status
  step_name text not null,
  status text not null check (status in ('started', 'succeeded', 'failed', 'retrying', 'skipped', 'compensated')),
  attempt int not null default 1 check (attempt >= 1),
  duration_ms int check (duration_ms is null or duration_ms >= 0),

  -- Emission source
  source_system text not null check (source_system in ('n8n', 'planner', 'developer', 'reviewer', 'deployer', 'jira', 'github', 'render', 'multiagent-api')),

  -- Idempotency dedupe key (optional)
  idempotency_key text,

  -- External ids
  jira_issue_id text,
  jira_issue_key text,
  github_repo text,
  github_branch text,
  github_commit_sha text,
  github_pr_number int,
  github_workflow_run_id text,
  deployment_provider text,
  deployment_id text,
  production_url text,

  -- Error data
  error_code text,
  error_message text,

  -- Useful context only (no secrets)
  metadata jsonb not null default '{}'::jsonb
);

-- Indexing for hot query patterns
create index if not exists idx_app_runs_user_time
  on observability.app_runs (user_id, requested_at desc);

create index if not exists idx_app_runs_user_ref_hash_time
  on observability.app_runs (user_ref_hash, requested_at desc);

create index if not exists idx_app_runs_status_time
  on observability.app_runs (final_status, requested_at desc);

create index if not exists idx_app_runs_n8n_execution
  on observability.app_runs (n8n_execution_id);

create index if not exists idx_trace_run_time
  on observability.app_trace_events (run_id, occurred_at);

create index if not exists idx_trace_step_time
  on observability.app_trace_events (step_name, occurred_at desc);

create index if not exists idx_trace_failed_time
  on observability.app_trace_events (occurred_at desc)
  where status = 'failed';

create index if not exists idx_trace_source_time
  on observability.app_trace_events (source_system, occurred_at desc);

create index if not exists idx_trace_jira_key
  on observability.app_trace_events (jira_issue_key);

create index if not exists idx_trace_github_commit
  on observability.app_trace_events (github_commit_sha);

create unique index if not exists idx_trace_run_idempotency_unique
  on observability.app_trace_events (run_id, idempotency_key)
  where idempotency_key is not null;

-- RLS baseline
alter table observability.app_runs enable row level security;
alter table observability.app_trace_events enable row level security;

-- Avoid accidental broad grants
revoke all on schema observability from public;
revoke all on observability.app_runs from public;
revoke all on observability.app_trace_events from public;

-- Service role can fully manage trace data.
create policy app_runs_service_role_all
  on observability.app_runs
  as permissive
  for all
  to service_role
  using (true)
  with check (true);

create policy app_trace_events_service_role_all
  on observability.app_trace_events
  as permissive
  for all
  to service_role
  using (true)
  with check (true);

-- Authenticated users can only read their own runs.
create policy app_runs_authenticated_select_own
  on observability.app_runs
  as permissive
  for select
  to authenticated
  using (auth.uid() = user_id);

create policy app_trace_events_authenticated_select_own
  on observability.app_trace_events
  as permissive
  for select
  to authenticated
  using (
    exists (
      select 1
      from observability.app_runs r
      where r.run_id = app_trace_events.run_id
        and r.user_id = auth.uid()
    )
  );

-- Explicit grants for Data API access with RLS enforcement.
grant usage on schema observability to authenticated, service_role;
grant select on observability.app_runs to authenticated;
grant select on observability.app_trace_events to authenticated;
grant all privileges on observability.app_runs to service_role;
grant all privileges on observability.app_trace_events to service_role;

-- Retention helper (365 days default)
create or replace function observability.purge_old_trace_data(retention_days int default 365)
returns table(deleted_events bigint, deleted_runs bigint)
language plpgsql
security definer
set search_path = observability, public
as $$
declare
  v_deleted_events bigint := 0;
  v_deleted_runs bigint := 0;
begin
  delete from observability.app_trace_events
  where occurred_at < now() - make_interval(days => retention_days);
  get diagnostics v_deleted_events = row_count;

  delete from observability.app_runs
  where requested_at < now() - make_interval(days => retention_days)
    and final_status in ('success', 'failed', 'cancelled');
  get diagnostics v_deleted_runs = row_count;

  return query select v_deleted_events, v_deleted_runs;
end;
$$;

revoke all on function observability.purge_old_trace_data(int) from public;
grant execute on function observability.purge_old_trace_data(int) to service_role;

comment on schema observability is 'End-to-end traceability for app lifecycle runs and events.';
comment on table observability.app_runs is 'One row per orchestration run.';
comment on table observability.app_trace_events is 'Append-only timeline events per run.';
