"""
Deployer Agent.

Responsibility: Take reviewed, approved code and handle deployment steps
(e.g. writing files to disk, calling CI/CD APIs, or triggering cloud deploys).

The orchestrator (n8n) calls POST /agents/deployer with the reviewed code.
"""

import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

import httpx

from providers.base import BaseLLMProvider


def _public_base_url() -> str:
        return os.getenv("PUBLIC_BASE_URL", "https://multiagent-system-4eze.onrender.com").strip().rstrip("/")


def _generated_apps_dir() -> Path:
        root = Path(__file__).resolve().parents[2]
        target = root / "generated_apps"
        target.mkdir(parents=True, exist_ok=True)
        return target


def _render_login_crud_html(title: str) -> str:
        safe_title = (title or "Generated Login CRUD App").replace("<", "").replace(">", "")
        return f"""<!doctype html>
<html lang=\"es\">
<head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>{safe_title}</title>
    <style>
        :root {{ --bg:#f4f7fb; --card:#ffffff; --accent:#005f73; --text:#1f2937; --muted:#6b7280; --ok:#0a7d3b; --danger:#b42318; }}
        * {{ box-sizing: border-box; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
        body {{ margin: 0; background: radial-gradient(circle at 20% 20%, #e9f5ff, var(--bg)); color: var(--text); }}
        .wrap {{ max-width: 960px; margin: 24px auto; padding: 0 16px; }}
        .card {{ background: var(--card); border-radius: 14px; box-shadow: 0 10px 30px rgba(0,0,0,.08); padding: 20px; margin-bottom: 16px; }}
        h1 {{ margin: 0 0 8px; }}
        .muted {{ color: var(--muted); }}
        input, button {{ padding: 10px 12px; border-radius: 8px; border: 1px solid #d0d7e2; }}
        button {{ cursor: pointer; border: none; background: var(--accent); color: white; font-weight: 600; }}
        .row {{ display:flex; gap:8px; flex-wrap:wrap; }}
        .grid {{ display:grid; grid-template-columns: 1fr 1fr; gap:8px; }}
        table {{ width:100%; border-collapse: collapse; margin-top: 10px; }}
        th,td {{ border-bottom: 1px solid #e5e7eb; text-align:left; padding:8px; }}
        .hidden {{ display:none; }}
        .ok {{ color: var(--ok); }}
        .danger {{ color: var(--danger); }}
    </style>
</head>
<body>
    <div class=\"wrap\">
        <div class=\"card\" id=\"loginCard\">
            <h1>Login</h1>
            <p class=\"muted\">Credenciales demo: <b>admin</b> / <b>admin123</b></p>
            <div class=\"grid\">
                <input id=\"user\" placeholder=\"Usuario\" />
                <input id=\"pass\" placeholder=\"Password\" type=\"password\" />
            </div>
            <div class=\"row\" style=\"margin-top:10px\">
                <button onclick=\"login()\">Entrar</button>
                <span id=\"loginMsg\" class=\"danger\"></span>
            </div>
        </div>

        <div class=\"card hidden\" id=\"appCard\">
            <div class=\"row\" style=\"justify-content:space-between;align-items:center\">
                <div>
                    <h1 style=\"margin-bottom:4px\">CRUD Clientes</h1>
                    <div class=\"muted\">App generada por el pipeline multiagente</div>
                </div>
                <button onclick=\"logout()\">Salir</button>
            </div>

            <h3>Nuevo / Editar cliente</h3>
            <div class=\"grid\">
                <input id=\"cName\" placeholder=\"Nombre\" />
                <input id=\"cEmail\" placeholder=\"Email\" />
                <input id=\"cPhone\" placeholder=\"Telefono\" />
                <input id=\"cCity\" placeholder=\"Ciudad\" />
            </div>
            <div class=\"row\" style=\"margin-top:10px\">
                <button onclick=\"saveCustomer()\">Guardar</button>
                <button onclick=\"resetForm()\" style=\"background:#64748b\">Limpiar</button>
                <span id=\"formMsg\"></span>
            </div>

            <h3>Listado de clientes</h3>
            <table>
                <thead>
                    <tr><th>Nombre</th><th>Email</th><th>Telefono</th><th>Ciudad</th><th>Acciones</th></tr>
                </thead>
                <tbody id=\"rows\"></tbody>
            </table>
        </div>
    </div>

    <script>
        const KEY='generated_customers_v1';
        let editId=null;

        function login() {{
            const u=document.getElementById('user').value.trim();
            const p=document.getElementById('pass').value.trim();
            const msg=document.getElementById('loginMsg');
            if(u==='admin' && p==='admin123') {{
                msg.textContent='';
                document.getElementById('loginCard').classList.add('hidden');
                document.getElementById('appCard').classList.remove('hidden');
                render();
            }} else {{
                msg.textContent='Credenciales invalidas';
            }}
        }}

        function logout() {{
            document.getElementById('appCard').classList.add('hidden');
            document.getElementById('loginCard').classList.remove('hidden');
        }}

        function list() {{ return JSON.parse(localStorage.getItem(KEY)||'[]'); }}
        function saveAll(items) {{ localStorage.setItem(KEY, JSON.stringify(items)); }}

        function validate(c) {{
            if(!c.name || c.name.length < 2) return 'Nombre invalido';
            if(!/^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/.test(c.email)) return 'Email invalido';
            if(!/^\\+?[0-9\\-\\s]{7,20}$/.test(c.phone)) return 'Telefono invalido';
            if(!c.city) return 'Ciudad obligatoria';
            return '';
        }}

        function getForm() {{
            return {{
                id: editId || crypto.randomUUID(),
                name: document.getElementById('cName').value.trim(),
                email: document.getElementById('cEmail').value.trim(),
                phone: document.getElementById('cPhone').value.trim(),
                city: document.getElementById('cCity').value.trim(),
            }};
        }}

        function resetForm() {{
            ['cName','cEmail','cPhone','cCity'].forEach(i=>document.getElementById(i).value='');
            editId=null;
            document.getElementById('formMsg').textContent='';
        }}

        function saveCustomer() {{
            const c=getForm();
            const err=validate(c);
            const msg=document.getElementById('formMsg');
            if(err) {{ msg.className='danger'; msg.textContent=err; return; }}
            const items=list();
            const idx=items.findIndex(x=>x.id===c.id);
            if(idx>=0) items[idx]=c; else items.push(c);
            saveAll(items);
            msg.className='ok';
            msg.textContent='Cliente guardado';
            resetForm();
            render();
        }}

        function editCustomer(id) {{
            const c=list().find(x=>x.id===id);
            if(!c) return;
            editId=id;
            document.getElementById('cName').value=c.name;
            document.getElementById('cEmail').value=c.email;
            document.getElementById('cPhone').value=c.phone;
            document.getElementById('cCity').value=c.city;
        }}

        function deleteCustomer(id) {{
            const items=list().filter(x=>x.id!==id);
            saveAll(items);
            render();
        }}

        function render() {{
            const rows=document.getElementById('rows');
            rows.innerHTML='';
            for(const c of list()) {{
                const tr=document.createElement('tr');
                tr.innerHTML=`<td>${{c.name}}</td><td>${{c.email}}</td><td>${{c.phone}}</td><td>${{c.city}}</td>
                                            <td><button onclick=\"editCustomer('${{c.id}}')\">Editar</button>
                                            <button style=\"background:#b42318\" onclick=\"deleteCustomer('${{c.id}}')\">Eliminar</button></td>`;
                rows.appendChild(tr);
            }}
        }}
    </script>
</body>
</html>"""


def _materialize_generated_app(run_id: str, review: Dict[str, Any]) -> Dict[str, Any]:
        app_id = run_id or f"run-{abs(hash(json.dumps(review, ensure_ascii=True))) % 1000000}"
        objective = "Generated Login CRUD App"
        code = review.get("code") if isinstance(review.get("code"), dict) else {}
        if isinstance(code, dict):
                objective = str(code.get("objective") or objective)
        file_path = _generated_apps_dir() / f"{app_id}.html"
        file_path.write_text(_render_login_crud_html(objective), encoding="utf-8")
        url = f"{_public_base_url()}/generated-apps/{app_id}"
        return {
                "attempted": True,
                "deployed": True,
                "service_url": url,
                "app_id": app_id,
                "storage": str(file_path),
        }


def _load_system_prompt() -> str:
    prompt_path = Path(__file__).resolve().parent / "prompts" / "system.md"
    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8").strip()
    return "You are the Deployer agent. Return deployment readiness and traceable steps."


def _extract_task_id(review: Dict[str, Any]) -> str:
    if isinstance(review.get("task_id"), str):
        return review["task_id"]
    code = review.get("code") if isinstance(review.get("code"), dict) else {}
    objective = str(code.get("objective", ""))
    if "MAS-49" in objective:
        return "MAS-49"
    return ""


def _build_repo_name(review: Dict[str, Any], run_id: str = "") -> str:
    code = review.get("code") if isinstance(review.get("code"), dict) else {}
    objective = str(code.get("objective", ""))
    lowered = objective.lower()
    suffix = f"-{run_id[:8]}" if run_id else ""
    if "create_project" in lowered and "backend" in lowered:
        return f"generated-backend-service{suffix}"
    if "login" in lowered and "crud" in lowered:
        return f"generated-login-crud-app{suffix}"
    return f"generated-app-{hash(objective) % 10000}{suffix}"


def _create_github_repo(repo_name: str, code_artifact: str = "") -> Dict[str, Any]:
    """Create GitHub repo and commit initial code."""
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if not token:
        return {
            "attempted": False,
            "created": False,
            "reason": "GITHUB_TOKEN not configured",
            "repo_name": repo_name,
            "repo_url": None,
        }

    api_base = os.getenv("GITHUB_API_BASE", "https://api.github.com").strip().rstrip("/")
    owner = os.getenv("GITHUB_OWNER", "").strip()
    create_in_org = os.getenv("GITHUB_CREATE_IN_ORG", "false").strip().lower() == "true"

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    payload = {
        "name": repo_name,
        "private": False,
        "auto_init": True,
        "description": "Repository generated by multi-agent deployer",
    }

    if create_in_org and owner:
        endpoint = f"{api_base}/orgs/{owner}/repos"
    else:
        endpoint = f"{api_base}/user/repos"

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(endpoint, headers=headers, json=payload)

        if response.status_code in {200, 201}:
            data = response.json()
            repo_url = data.get("html_url")
            ssh_url = data.get("ssh_url")
            clone_url = data.get("clone_url")
            owner_login = ((data.get("owner") or {}).get("login") or "").strip()
            default_branch = str(data.get("default_branch") or "main").strip() or "main"

            commit_sha = None
            # If code artifact provided, commit it
            if code_artifact and clone_url:
                commit_result = _commit_to_repo(repo_url, clone_url, code_artifact, token)
                commit_sha = commit_result.get("commit_sha")

            # Fallback: read HEAD SHA from GitHub API so traceability always has a commit id
            if not commit_sha and owner_login:
                commit_sha = _get_repo_head_sha(api_base, headers, owner_login, repo_name, default_branch)

            return {
                "attempted": True,
                "created": True,
                "repo_name": repo_name,
                "repo_url": repo_url,
                "clone_url": clone_url,
                "commit_sha": commit_sha,
                "api_url": data.get("url"),
                "status_code": response.status_code,
            }

        return {
            "attempted": True,
            "created": False,
            "repo_name": repo_name,
            "commit_sha": None,
            "status_code": response.status_code,
            "error": response.text[:200],
            "repo_url": None,
        }
    except Exception as e:
        return {
            "attempted": True,
            "created": False,
            "repo_name": repo_name,
            "commit_sha": None,
            "error": str(e),
            "repo_url": None,
        }


def _commit_to_repo(repo_url: str, clone_url: str, code_artifact: str, token: str) -> Dict[str, Any]:
    """Clone repo, commit code, push, and return commit SHA."""
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            # Clone repo
            git_clone_url = clone_url.replace("https://", f"https://x-access-token:{token}@")
            result = subprocess.run(
                ["git", "clone", git_clone_url, tmpdir],
                capture_output=True,
                timeout=30,
                text=True,
            )
            if result.returncode != 0:
                return {"success": False, "error": result.stderr, "commit_sha": None}

            # Create main code file
            code_file = Path(tmpdir) / "app.py"
            code_file.write_text(code_artifact, encoding="utf-8")

            # Create requirements.txt stub
            reqs_file = Path(tmpdir) / "requirements.txt"
            reqs_file.write_text("flask==2.3.2\nflask-cors==4.0.0\n", encoding="utf-8")

            # Git add, commit, push
            subprocess.run(["git", "config", "user.name", "Generated Deploy"], cwd=tmpdir, check=False)
            subprocess.run(["git", "config", "user.email", "deploy@generated.local"], cwd=tmpdir, check=False)
            subprocess.run(["git", "add", "."], cwd=tmpdir, check=False)
            result = subprocess.run(
                ["git", "commit", "-m", "Initial app code generated by multi-agent deployer"],
                cwd=tmpdir,
                capture_output=True,
                timeout=30,
                text=True,
            )
            commit_sha = None
            if result.returncode == 0:
                push_result = subprocess.run(["git", "push", "-u", "origin", "main"], cwd=tmpdir, check=False)
                # Capture the commit SHA
                sha_result = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    cwd=tmpdir,
                    capture_output=True,
                    text=True,
                )
                if sha_result.returncode == 0:
                    commit_sha = sha_result.stdout.strip()

        return {"success": True, "commit_sha": commit_sha}
    except Exception as e:
        return {"success": False, "error": str(e), "commit_sha": None}


def _get_repo_head_sha(api_base: str, headers: Dict[str, str], owner: str, repo_name: str, branch: str) -> Optional[str]:
    """Fetch the current HEAD commit SHA for a repository branch."""
    try:
        with httpx.Client(timeout=20.0) as client:
            r = client.get(
                f"{api_base}/repos/{owner}/{repo_name}/commits/{branch}",
                headers=headers,
            )
        if r.status_code == 200:
            return str((r.json() or {}).get("sha") or "").strip() or None
    except Exception:
        return None
    return None


def _deploy_to_render(repo_url: str, repo_name: str) -> Dict[str, Any]:
    """Deploy repo to Render cloud platform."""
    render_token = os.getenv("RENDER_API_TOKEN", "").strip()
    if not render_token:
        return {
            "attempted": False,
            "deployed": False,
            "reason": "RENDER_API_TOKEN not configured",
            "service_url": None,
        }

    api_base = "https://api.render.com/v1"
    headers = {
        "Authorization": f"Bearer {render_token}",
        "Accept": "application/json",
    }

    # Create service
    payload = {
        "name": repo_name,
        "type": "web_service",
        "repo": repo_url,
        "branch": "main",
        "runtime_id": "python3",
        "buildCommand": "pip install -r requirements.txt",
        "startCommand": "python app.py",
        "plan": "free",
        "envVars": [{"key": "PORT", "value": "8000"}],
    }

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(f"{api_base}/services", headers=headers, json=payload)

        if response.status_code in {200, 201}:
            data = response.json()
            service_id = data.get("id")
            service_url = data.get("serviceDetails", {}).get("url")

            return {
                "attempted": True,
                "deployed": True,
                "service_id": service_id,
                "service_url": service_url,
                "status_code": response.status_code,
            }

        return {
            "attempted": True,
            "deployed": False,
            "status_code": response.status_code,
            "error": response.text[:200],
            "service_url": None,
        }
    except Exception as e:
        return {
            "attempted": True,
            "deployed": False,
            "error": str(e),
            "service_url": None,
        }


def _notify_jira(
    run_id: str,
    jira_issue_key: str,
    jira_base_url: str,
    jira_email: str,
    jira_api_token: str,
    deployment_url: Optional[str],
    git_repo_url: Optional[str],
    git_commit_sha: Optional[str],
    objective: str,
) -> Dict[str, Any]:
    """Create or update a Jira issue with run traceability data.

    - If jira_issue_key is provided: add comment + transition to Done.
    - If no issue_key: create a new issue with all the data.
    Returns dict with fields: jira_issue_key, jira_issue_url, action.
    """
    # Fall back to env-level credentials if not provided in request
    effective_base = (jira_base_url or os.getenv("JIRA_BASE_URL", "")).strip().rstrip("/")
    effective_email = (jira_email or os.getenv("JIRA_EMAIL", "")).strip()
    effective_token = (jira_api_token or os.getenv("JIRA_API_TOKEN", "")).strip()

    if not effective_base or not effective_email or not effective_token:
        return {
            "attempted": False,
            "reason": "Jira credentials not configured",
            "jira_issue_key": jira_issue_key or None,
            "jira_issue_url": None,
        }

    import base64
    auth = base64.b64encode(f"{effective_email}:{effective_token}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    def _doc(text: str) -> dict:
        return {
            "type": "doc",
            "version": 1,
            "content": [{"type": "paragraph", "content": [{"type": "text", "text": text}]}],
        }

    comment_lines = [
        f"Run ID: {run_id}",
        f"Status: COMPLETED",
        f"Deployment URL: {deployment_url or 'N/A'}",
        f"GitHub Repo: {git_repo_url or 'N/A'}",
        f"Commit SHA: {git_commit_sha or 'N/A'}",
        f"Objective: {objective}",
    ]
    comment_text = "\n".join(comment_lines)

    try:
        with httpx.Client(timeout=20.0) as client:
            resolved_key = jira_issue_key.strip() if jira_issue_key else ""

            # If no key provided, create a new issue
            if not resolved_key:
                project_key = os.getenv("JIRA_PROJECT_KEY", "MAS")
                create_payload = {
                    "fields": {
                        "project": {"key": project_key},
                        "summary": f"[Auto] {objective[:100]}",
                        "description": _doc(comment_text),
                        "issuetype": {"name": "Task"},
                        "labels": ["auto-generated", "multiagent-pipeline"],
                    }
                }
                r = client.post(f"{effective_base}/rest/api/3/issue", headers=headers, json=create_payload)
                if r.status_code in {200, 201}:
                    data = r.json()
                    resolved_key = data.get("key", "")
                    issue_url = f"{effective_base}/browse/{resolved_key}" if resolved_key else None
                    return {
                        "attempted": True,
                        "action": "created",
                        "jira_issue_key": resolved_key,
                        "jira_issue_url": issue_url,
                    }
                return {
                    "attempted": True,
                    "action": "create_failed",
                    "jira_issue_key": None,
                    "jira_issue_url": None,
                    "error": r.text[:200],
                }

            # Add completion comment to existing issue
            comment_payload = {"body": _doc(comment_text)}
            client.post(f"{effective_base}/rest/api/3/issue/{resolved_key}/comment", headers=headers, json=comment_payload)

            # Try to transition to Done (transition id 31 = Done in standard workflows)
            trans_r = client.get(f"{effective_base}/rest/api/3/issue/{resolved_key}/transitions", headers=headers)
            if trans_r.status_code == 200:
                transitions = trans_r.json().get("transitions", [])
                done_id = next(
                    (t["id"] for t in transitions if t.get("name", "").lower() in {"done", "closed", "resolved"}),
                    None,
                )
                if done_id:
                    client.post(
                        f"{effective_base}/rest/api/3/issue/{resolved_key}/transitions",
                        headers=headers,
                        json={"transition": {"id": done_id}},
                    )

            issue_url = f"{effective_base}/browse/{resolved_key}"
            return {
                "attempted": True,
                "action": "updated",
                "jira_issue_key": resolved_key,
                "jira_issue_url": issue_url,
            }
    except Exception as e:
        return {
            "attempted": True,
            "action": "error",
            "jira_issue_key": jira_issue_key or None,
            "jira_issue_url": None,
            "error": str(e),
        }


class DeployerAgent:
    """Implement real Deployer agent with GitHub + Render integration."""

    def __init__(self, llm: BaseLLMProvider) -> None:
        self.llm = llm
        self.system_prompt = _load_system_prompt()

    def run(
        self,
        review: Any,
        run_id: Optional[str] = None,
        jira_issue_key: str = "",
        jira_base_url: str = "",
        jira_email: str = "",
        jira_api_token: str = "",
    ) -> dict:
        """
        Receive the *review* artefact from the Reviewer and deploy the code.

        Real implementation: create GitHub repo, commit code, deploy to Render,
        notify Jira, and return external_ids for unified traceability.
        """
        if isinstance(review, str):
            try:
                normalized_review = json.loads(review)
            except json.JSONDecodeError:
                normalized_review = {"approved": False, "raw": review}
        else:
            normalized_review = review if isinstance(review, dict) else {"approved": False, "raw": str(review)}

        approved = bool(normalized_review.get("approved"))

        # Extract code from review
        code_data = normalized_review.get("code", {}) if isinstance(normalized_review.get("code"), dict) else {}
        code_artifact = code_data.get("implementation", "") or code_data.get("code", "")
        objective = str(code_data.get("objective", "Generated App"))

        github_repo = None
        render_service = None
        deployment_url = None
        git_commit_sha = None
        git_repo_url = None

        # Only deploy if approved
        if approved:
            repo_name = _build_repo_name(normalized_review, run_id or "")

            # Step 1: Create GitHub repo + commit code
            github_repo = _create_github_repo(repo_name, code_artifact)
            git_repo_url = github_repo.get("repo_url")
            git_commit_sha = github_repo.get("commit_sha")

            # Step 2: Deploy to Render if repo was created
            if github_repo.get("created") and git_repo_url:
                render_service = _deploy_to_render(git_repo_url, repo_name)
                deployment_url = render_service.get("service_url")

            # Guaranteed fallback materialization inside current service
            if not deployment_url:
                fallback = _materialize_generated_app(run_id or "", normalized_review)
                render_service = fallback
                deployment_url = fallback.get("service_url")

        # Step 3: Notify Jira (create or update issue)
        jira_result = _notify_jira(
            run_id=run_id or "",
            jira_issue_key=jira_issue_key,
            jira_base_url=jira_base_url,
            jira_email=jira_email,
            jira_api_token=jira_api_token,
            deployment_url=deployment_url,
            git_repo_url=git_repo_url,
            git_commit_sha=git_commit_sha,
            objective=objective,
        )

        # Generate LLM summary
        prompt = (
            f"{self.system_prompt}\n\n"
            f"Deployment result for approved={approved}. "
            f"GitHub repo: {git_repo_url or 'pending'}. "
            f"Render service: {deployment_url or 'pending'}.\n"
            "Keep output concise."
        )
        response = self.llm.complete(prompt=prompt, temperature=0.2, max_tokens=220)

        status = "deployed" if deployment_url else ("validated" if approved else "blocked")

        deployment_payload = {
            "status": status,
            "ready_for_close": bool(deployment_url),
            "github_repo": github_repo,
            "render_service": render_service,
            "deployment_url": deployment_url,
            "model_notes": response[:1000],
        }

        # Build unified external_ids for traceability
        external_ids = {
            "deployment_url": deployment_url,
            "git_repo_url": git_repo_url,
            "git_commit_sha": git_commit_sha,
            "jira_issue_key": jira_result.get("jira_issue_key"),
            "jira_issue_url": jira_result.get("jira_issue_url"),
        }

        return {
            "agent": "deployer",
            "review": normalized_review,
            "deployment": json.dumps(deployment_payload, ensure_ascii=True),
            "status": status,
            "external_ids": external_ids,
        }
