"""Filesystem storage for research report team runs."""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from contracts import DEFAULT_ARTIFACT_TEMPLATES, artifact_manifest, public_roles
from docx_writer import write_minimal_docx


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


class RunStore:
    def __init__(self, runs_dir: Path) -> None:
        self.runs_dir = runs_dir
        self.runs_dir.mkdir(parents=True, exist_ok=True)

    def create_run(self, run_id: str, title: str, brief: str, mode: str) -> Path:
        run_dir = self.runs_dir / run_id
        (run_dir / "prompts").mkdir(parents=True, exist_ok=False)
        (run_dir / "artifacts").mkdir(parents=True, exist_ok=True)
        created_at = now_iso()

        task = {
            "id": run_id,
            "created_at": created_at,
            "title": title,
            "brief": brief,
            "workflow": "codex-quality-first-local-web",
            "mode": mode,
            "api_calls": False,
            "outputs": {
                "final_markdown": "artifacts/08_final.md",
                "final_docx": "artifacts/08_final.docx",
                "final_manifest": "artifacts/08_final_manifest.json",
            },
            "roles": public_roles(),
        }
        status = initial_status(run_id, created_at)
        self.write_json(run_dir / "task.json", task)
        self.write_json(run_dir / "status.json", status)
        return run_dir

    def scaffold_workspace(
        self,
        run_dir: Path,
        title: str,
        brief: str,
        workflow: str,
        auto_progress: bool,
    ) -> tuple[dict[str, str], dict[str, str]]:
        (run_dir / "prompts").mkdir(parents=True, exist_ok=True)
        (run_dir / "artifacts").mkdir(parents=True, exist_ok=True)
        prompt_paths: dict[str, str] = {}
        artifact_paths: dict[str, str] = {}
        created_at = now_iso()

        for role in public_roles():
            rel = role["prompt"]
            if rel:
                prompt_paths[role["key"]] = rel
                self.atomic_write_text(run_dir / rel, _scaffold_prompt(title, brief, workflow, role))

        for filename, template in DEFAULT_ARTIFACT_TEMPLATES.items():
            rel = f"artifacts/{filename}"
            artifact_paths[filename] = rel
            self.atomic_write_text(run_dir / rel, template)

        docx_rel = "artifacts/08_final.docx"
        write_minimal_docx(run_dir / docx_rel, title=title, body="TBD")
        artifact_paths["08_final.docx"] = docx_rel

        task = {
            "created_at": created_at,
            "title": title,
            "brief": brief,
            "workflow": workflow,
            "mode": "quality-first",
            "api_calls": False,
            "auto_progress": auto_progress,
            "outputs": {
                "final_markdown": "artifacts/08_final.md",
                "final_docx": "artifacts/08_final.docx",
                "final_manifest": "artifacts/08_final_manifest.json",
            },
            "roles": public_roles(),
            "prompts": prompt_paths,
            "artifacts": artifact_paths,
            "status": "status.json",
        }
        status = initial_status(run_dir.name, created_at)
        status.update(
            {
                "state": "intake",
                "current_role": "manager",
                "auto_progress": auto_progress,
                "docx_status": "placeholder",
                "next_step": "Open prompts/00_manager.md and start the task in Codex.",
            }
        )
        self.write_json(run_dir / "task.json", task)
        self.write_json(run_dir / "status.json", status)
        self.atomic_write_text(run_dir / "sources.md", "# Sources\n\n- TBD\n")
        return prompt_paths, artifact_paths

    def get_run(self, run_id: str) -> dict[str, Any]:
        run_dir = self.run_dir(run_id)
        status = self.read_json(run_dir / "status.json")
        return {
            "id": run_id,
            "task": self.read_json(run_dir / "task.json"),
            "status": status,
            "roles": public_roles(),
            "files": self.file_map(run_dir),
            "artifact_manifest": artifact_manifest(run_dir),
            "quality_gate": status.get("quality_gate", {}),
            "docx_status": status.get("docx_status", "missing"),
            "revision_count": status.get("revision_count", 0),
        }

    def list_runs(self) -> list[dict[str, Any]]:
        runs = []
        for path in sorted(self.runs_dir.iterdir(), reverse=True):
            if not path.is_dir():
                continue
            try:
                runs.append(self.get_run(path.name))
            except (OSError, ValueError, json.JSONDecodeError):
                continue
        return runs[:30]

    def run_dir(self, run_id: str) -> Path:
        if not run_id or "/" in run_id or "\\" in run_id or ".." in run_id:
            raise ValueError("invalid run id")
        run_dir = safe_child(self.runs_dir, run_id)
        if not run_dir.is_dir():
            raise FileNotFoundError(run_id)
        return run_dir

    def read_file(self, run_id: str, relative_path: str) -> str:
        target = safe_child(self.run_dir(run_id), relative_path)
        if not target.is_file():
            raise FileNotFoundError(relative_path)
        return target.read_text(encoding="utf-8")

    def update_status(self, run_dir: Path, **updates: Any) -> dict[str, Any]:
        status_path = run_dir / "status.json"
        status = self.read_json(status_path)
        status.update(updates)
        status["updated_at"] = now_iso()
        self.write_json(status_path, status)
        return status

    def append_agent_run(
        self,
        run_dir: Path,
        entry: dict[str, Any],
        artifact_paths: list[str],
        usage: dict[str, int] | None,
    ) -> None:
        status_path = run_dir / "status.json"
        status = self.read_json(status_path)
        status["completed_roles"] = [*status.get("completed_roles", []), entry["key"]]
        if usage:
            entry["usage"] = usage
        status.setdefault("agent_runs", []).append(entry)
        artifacts = status.setdefault("artifacts", {})
        for path in artifact_paths:
            target = run_dir / "artifacts" / path
            artifacts[f"artifacts/{path}"] = {
                "exists": target.is_file(),
                "size": target.stat().st_size if target.is_file() else 0,
            }
        status["updated_at"] = now_iso()
        self.write_json(status_path, status)

    def append_event(self, run_dir: Path, event: dict[str, Any]) -> None:
        event = {"time": now_iso(), **event}
        with (run_dir / "events.ndjson").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")

    def file_map(self, run_dir: Path) -> dict[str, bool]:
        return {item["path"]: item["exists"] for item in artifact_manifest(run_dir)}

    def read_json(self, path: Path) -> dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8"))

    def write_json(self, path: Path, payload: dict[str, Any]) -> None:
        self.atomic_write_text(path, json.dumps(payload, ensure_ascii=False, indent=2))

    def atomic_write_text(self, path: Path, text: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(f".{path.name}.tmp")
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, path)


def initial_status(run_id: str, created_at: str) -> dict[str, Any]:
    return {
        "id": run_id,
        "created_at": created_at,
        "updated_at": created_at,
        "state": "queued",
        "current_role": "",
        "current_role_started_at": "",
        "completed_roles": [],
        "failed_role": "",
        "revision_count": 0,
        "pending_user_feedback": False,
        "auto_progress": True,
        "agent_runs": [],
        "artifacts": {},
        "loop_state": {
            "max_attempts_per_gate": 2,
            "retry_counts": {},
            "iterations": [],
        },
        "unresolved_gate_issues": [],
        "task_contract": {},
        "evidence_gate": {"decision": "not_started"},
        "analysis_gate": {"decision": "not_started"},
        "review_gate": {"decision": "not_started"},
        "revision_status": {"required": False, "status": "not_started"},
        "final_gate": {"decision": "not_started"},
        "quality_gate": {"decision": "not_started"},
        "selected_final_candidate": "",
        "docx_status": "missing",
        "error": "",
    }


def safe_child(root: Path, relative_path: str) -> Path:
    root_resolved = root.resolve()
    target = (root_resolved / relative_path).resolve()
    if root_resolved != target and root_resolved not in target.parents:
        raise ValueError("path escapes allowed directory")
    return target


def _scaffold_prompt(title: str, brief: str, workflow: str, role: dict[str, Any]) -> str:
    return (
        "# Task Context\n\n"
        f"- Title: {title}\n"
        f"- User request: {brief}\n"
        f"- Workflow: {workflow}\n"
        f"- Role: {role['role']}\n"
        f"- Target artifact: {role['artifact']}\n"
        "- This CLI creates workspace files only; it does not execute agents.\n"
        "- Treat artifacts/00_task_brief.md as the shared context packet.\n"
    )
