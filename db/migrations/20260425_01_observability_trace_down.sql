-- Observability trace schema rollback (DOWN migration)
-- Date: 2026-04-25

revoke execute on function observability.purge_old_trace_data(int) from service_role;
drop function if exists observability.purge_old_trace_data(int);

drop policy if exists app_trace_events_authenticated_select_own on observability.app_trace_events;
drop policy if exists app_runs_authenticated_select_own on observability.app_runs;
drop policy if exists app_trace_events_service_role_all on observability.app_trace_events;
drop policy if exists app_runs_service_role_all on observability.app_runs;

drop table if exists observability.app_trace_events;
drop table if exists observability.app_runs;

drop schema if exists observability;
