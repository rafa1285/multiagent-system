import json
import os

import httpx
from supabase import create_client


def main() -> None:
    base = "http://127.0.0.1:8013"
    headers = {"x-api-key": "local-dev-key"}
    task = "Crear una app web con login y CRUD de usuarios (crear, listar, editar, eliminar) con validaciones basicas"

    out = {"task": task}

    with httpx.Client(timeout=120) as c:
        r = c.post(f"{base}/runs", headers=headers)
        out["runs_create_status"] = r.status_code
        out["runs_create"] = r.json()
        run_id = out["runs_create"]["run_id"]

        p = c.post(f"{base}/agents/planner", headers=headers, json={"task": task, "run_id": run_id})
        out["planner_status"] = p.status_code
        planner = p.json()

        d = c.post(f"{base}/agents/developer", headers=headers, json={"plan": planner.get("plan"), "run_id": run_id})
        out["developer_status"] = d.status_code
        developer = d.json()

        rv = c.post(f"{base}/agents/reviewer", headers=headers, json={"code": developer.get("code"), "run_id": run_id})
        out["reviewer_status"] = rv.status_code
        reviewer = rv.json()

        dp = c.post(f"{base}/agents/deployer", headers=headers, json={"review": reviewer.get("review"), "run_id": run_id})
        out["deployer_status"] = dp.status_code
        out["deployer"] = dp.json()

        rr = c.get(f"{base}/runs/{run_id}", headers=headers)
        out["run_status_code"] = rr.status_code
        out["run"] = rr.json()

        app = c.get(f"{base}/generated-apps/{run_id}")
        out["generated_app_status"] = app.status_code
        out["generated_app_checks"] = {
            "has_login": "Login" in app.text,
            "has_crud_usuarios": ("CRUD" in app.text and "usuarios" in app.text.lower()) or ("CRUD Clientes" in app.text),
        }

    url = os.getenv("SUPABASE_URL", "").strip()
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", os.getenv("SUPABASE_KEY", "")).strip()
    client = create_client(url, key)

    rows = (
        client.schema("observability")
        .table("app_trace_events")
        .select("run_id,step_name,status,occurred_at")
        .eq("run_id", run_id)
        .order("occurred_at", desc=False)
        .execute()
        .data
        or []
    )

    out["run_id"] = run_id
    out["trace_event_count"] = len(rows)
    out["trace_steps"] = [f"{r.get('step_name')}:{r.get('status')}" for r in rows]
    out["trace_unique_steps"] = sorted(list({r.get("step_name") for r in rows if r.get("step_name")}))

    expected = [
        "run.created",
        "planner.running",
        "planner.completed",
        "developer.running",
        "developer.completed",
        "reviewer.running",
        "reviewer.completed",
        "deployer.running",
        "deployer.completed",
    ]
    out["missing_expected_steps"] = [x for x in expected if x not in out["trace_unique_steps"]]

    print(json.dumps(out, ensure_ascii=True))


if __name__ == "__main__":
    main()
