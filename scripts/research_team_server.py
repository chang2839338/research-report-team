#!/usr/bin/env python3
"""Local web server for running the research-report-team through Codex."""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import shutil
import subprocess
import threading
import traceback
import urllib.parse
from dataclasses import dataclass
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


ROLES = [
    {
        "key": "manager",
        "role": "Manager",
        "display_role": "Manager",
        "label": "Task Brief",
        "prompt": "manager.md",
        "prompt_file": "01_manager.md",
        "artifact": "00_task_brief.md",
        "inputs": [],
        "goal": "Create the task brief that will guide all later role work.",
    },
    {
        "key": "researcher",
        "role": "Researcher",
        "display_role": "Researcher",
        "label": "Research",
        "prompt": "researcher.md",
        "prompt_file": "02_researcher.md",
        "artifact": "01_research.md",
        "inputs": ["00_task_brief.md"],
        "goal": "Gather source-backed findings and uncertainty notes.",
    },
    {
        "key": "analyst",
        "role": "Analyst",
        "display_role": "Analyst",
        "label": "Analysis",
        "prompt": "analyst.md",
        "prompt_file": "03_analyst.md",
        "artifact": "02_analysis.md",
        "inputs": ["00_task_brief.md", "01_research.md"],
        "goal": "Turn the research into criteria, tradeoffs, risks, and recommendation.",
    },
    {
        "key": "writer",
        "role": "Writer",
        "display_role": "Writer",
        "label": "Draft",
        "prompt": "writer.md",
        "prompt_file": "04_writer.md",
        "artifact": "03_draft.md",
        "inputs": ["00_task_brief.md", "01_research.md", "02_analysis.md"],
        "goal": "Draft a decision-ready report from the brief, research, and analysis.",
    },
    {
        "key": "reviewer",
        "role": "Reviewer",
        "display_role": "Reviewer",
        "label": "Review",
        "prompt": "reviewer.md",
        "prompt_file": "05_reviewer.md",
        "artifact": "04_review.md",
        "inputs": ["00_task_brief.md", "01_research.md", "02_analysis.md", "03_draft.md"],
        "extra_inputs": ["references/report-quality-rubric.md"],
        "goal": "Review the draft against the quality rubric and request targeted revisions if needed.",
    },
    {
        "key": "final_manager",
        "role": "Manager",
        "display_role": "Final",
        "label": "Final Report",
        "prompt": "manager.md",
        "prompt_file": "06_final_manager.md",
        "artifact": "05_final.md",
        "inputs": ["00_task_brief.md", "01_research.md", "02_analysis.md", "03_draft.md", "04_review.md"],
        "goal": "Create the final Markdown report. Do not create a DOCX file.",
    },
]


@dataclass(frozen=True)
class ServerConfig:
    root: Path
    runs_dir: Path
    codex_bin: str
    codex_model: str
    codex_sandbox: str
    job_timeout: int


class ResearchTeamServer:
    def __init__(self, config: ServerConfig) -> None:
        self.config = config
        self.config.runs_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def create_run(self, title: str, brief: str) -> dict[str, Any]:
        title = title.strip() or "Untitled report"
        brief = brief.strip()
        if not brief:
            raise ValueError("보고서 내용을 입력하세요.")

        run_id = self._unique_run_id()
        run_dir = self.config.runs_dir / run_id
        for name in ["prompts", "artifacts"]:
            (run_dir / name).mkdir(parents=True, exist_ok=True)

        now = _now()
        _write_json(
            run_dir / "task.json",
            {
                "id": run_id,
                "created_at": now,
                "title": title,
                "brief": brief,
                "workflow": "codex-auto-local-web",
                "outputs": {"final_markdown": "artifacts/05_final.md"},
                "roles": _public_roles(),
            },
        )
        _write_json(
            run_dir / "status.json",
            {
                "id": run_id,
                "created_at": now,
                "updated_at": now,
                "state": "queued",
                "current_role": "",
                "completed_roles": [],
                "agent_runs": [],
                "error": "",
            },
        )

        threading.Thread(target=self._run_workflow, args=(run_id,), daemon=True).start()
        return self.get_run(run_id)

    def list_runs(self) -> list[dict[str, Any]]:
        runs = []
        for path in sorted(self.config.runs_dir.iterdir(), reverse=True):
            if not path.is_dir():
                continue
            try:
                runs.append(self.get_run(path.name))
            except (OSError, ValueError, json.JSONDecodeError):
                continue
        return runs[:30]

    def get_run(self, run_id: str) -> dict[str, Any]:
        run_dir = self._run_dir(run_id)
        return {
            "id": run_id,
            "task": _read_json(run_dir / "task.json"),
            "status": _read_json(run_dir / "status.json"),
            "roles": _public_roles(),
            "files": _file_manifest(run_dir),
        }

    def read_file(self, run_id: str, relative_path: str) -> str:
        target = _safe_child(self._run_dir(run_id), relative_path)
        if not target.is_file():
            raise FileNotFoundError(relative_path)
        return target.read_text(encoding="utf-8", errors="replace")

    def _run_workflow(self, run_id: str) -> None:
        run_dir = self._run_dir(run_id)
        task = _read_json(run_dir / "task.json")

        try:
            for role in ROLES:
                self._update_status(run_dir, state="running", current_role=role["key"])
                self._run_role(run_dir, task, role)
                self._append_agent_run(run_dir, role)
            self._update_status(run_dir, state="completed", current_role="", error="")
        except Exception:
            detail = traceback.format_exc().strip()
            (run_dir / "error.log").write_text(detail, encoding="utf-8", errors="replace")
            self._update_status(run_dir, state="failed", error=detail)

    def _run_role(self, run_dir: Path, task: dict[str, Any], role: dict[str, Any]) -> None:
        prompt = self._build_execution_prompt(role, task, run_dir)
        prompt_path = run_dir / "prompts" / role["prompt_file"]
        artifact_path = run_dir / "artifacts" / role["artifact"]
        last_message_path = artifact_path.with_suffix(".last.md")

        prompt_path.write_text(prompt, encoding="utf-8")
        result = self._run_codex(prompt, run_dir, last_message_path)
        reply = _strip_markdown_fence(_read_last_message(last_message_path))

        if result.returncode != 0:
            detail = _compact_codex_output(result)
            if reply:
                detail = f"{detail}\n\nLast message:\n{reply}".strip()
            raise RuntimeError(f"{role['role']} Codex exited {result.returncode}: {detail}")
        if not reply.strip():
            raise RuntimeError(f"{role['role']} returned an empty artifact")

        artifact_path.write_text(reply, encoding="utf-8")

    def _run_codex(self, prompt: str, cwd: Path, last_message_path: Path) -> subprocess.CompletedProcess[str]:
        command = [
            _resolve_codex_bin(self.config.codex_bin),
            "exec",
            "--skip-git-repo-check",
            "--sandbox",
            self.config.codex_sandbox,
            "--cd",
            str(cwd),
            "--color",
            "never",
            "--output-last-message",
            str(last_message_path),
        ]
        if self.config.codex_model:
            command.extend(["--model", self.config.codex_model])
        command.append("-")

        try:
            return subprocess.run(
                command,
                input=prompt,
                text=True,
                encoding="utf-8",
                errors="replace",
                cwd=str(cwd),
                capture_output=True,
                timeout=self.config.job_timeout,
                env=_utf8_environment(),
            )
        except FileNotFoundError as exc:
            raise FileNotFoundError(f"Codex 실행 파일을 찾을 수 없습니다: {command[0]!r}") from exc

    def _build_execution_prompt(self, role: dict[str, Any], task: dict[str, Any], run_dir: Path) -> str:
        role_prompt = (self.config.root / "prompts" / role["prompt"]).read_text(encoding="utf-8")
        context_parts = [
            "# Run Context",
            f"- Report title: {task['title']}",
            f"- User request: {task['brief']}",
            f"- Current role: {role['role']}",
            f"- Current step: {role['label']}",
            f"- Goal: {role['goal']}",
            f"- Output artifact: artifacts/{role['artifact']}",
            "- Output language: Korean unless the user request clearly requires another language.",
            "- This local web workflow creates Markdown only. Ignore any DOCX instructions in the role prompt.",
            "- Output only the Markdown body for the target artifact.",
            "- Do not wrap the answer in code fences.",
            "- Do not create DOCX files.",
            "- Do not edit local files; the server will save your final answer.",
            "",
            "# Role Prompt",
            role_prompt,
        ]

        for artifact in role.get("inputs", []):
            context_parts.extend(["", f"# Input: artifacts/{artifact}", _read_optional(run_dir / "artifacts" / artifact)])

        for extra in role.get("extra_inputs", []):
            context_parts.extend(["", f"# Reference: {extra}", _read_optional(self.config.root / extra)])

        if role["artifact"] == "05_final.md":
            context_parts.extend(
                [
                    "",
                    "# Final Report Instruction",
                    "Use the review notes to improve the draft before producing the final report. "
                    "If the review approved the draft, polish and finalize it. If the review requested "
                    "revisions, apply the smallest useful revision directly in the final report.",
                ]
            )

        return "\n".join(context_parts).strip() + "\n"

    def _unique_run_id(self) -> str:
        base = datetime.now().strftime("%Y%m%d_%H%M%S")
        with self._lock:
            run_id = base
            suffix = 1
            while (self.config.runs_dir / run_id).exists():
                suffix += 1
                run_id = f"{base}_{suffix:02d}"
            return run_id

    def _run_dir(self, run_id: str) -> Path:
        if not run_id or "/" in run_id or "\\" in run_id or ".." in run_id:
            raise ValueError("invalid run id")
        run_dir = _safe_child(self.config.runs_dir, run_id)
        if not run_dir.is_dir():
            raise FileNotFoundError(run_id)
        return run_dir

    def _update_status(self, run_dir: Path, **updates: Any) -> None:
        status_path = run_dir / "status.json"
        status = _read_json(status_path)
        status.update(updates)
        status["updated_at"] = _now()
        _write_json(status_path, status)

    def _append_agent_run(self, run_dir: Path, role: dict[str, Any]) -> None:
        status_path = run_dir / "status.json"
        status = _read_json(status_path)
        status["completed_roles"] = [*status.get("completed_roles", []), role["key"]]
        status.setdefault("agent_runs", []).append(
            {
                "key": role["key"],
                "role": role["role"],
                "label": role["label"],
                "artifact": f"artifacts/{role['artifact']}",
                "prompt": f"prompts/{role['prompt_file']}",
                "status": "completed",
                "completed_at": _now(),
            }
        )
        status["updated_at"] = _now()
        _write_json(status_path, status)


def make_handler(app: ResearchTeamServer) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        server_version = "ResearchTeamServer/1.0"

        def do_GET(self) -> None:
            parsed = urllib.parse.urlparse(self.path)
            try:
                if parsed.path == "/api/runs":
                    self._send_json(app.list_runs())
                    return
                if parsed.path.startswith("/api/runs/"):
                    parts = parsed.path.strip("/").split("/")
                    if len(parts) == 3:
                        self._send_json(app.get_run(parts[2]))
                        return
                    if len(parts) == 4 and parts[3] == "files":
                        query = urllib.parse.parse_qs(parsed.query)
                        self._send_text(app.read_file(parts[2], query.get("path", [""])[0]))
                        return
                self._serve_static(parsed.path)
            except FileNotFoundError:
                self._send_json({"error": "not found"}, status=404)
            except ValueError as exc:
                self._send_json({"error": str(exc)}, status=400)
            except Exception as exc:
                self._send_json({"error": str(exc)}, status=500)

        def do_POST(self) -> None:
            try:
                if urllib.parse.urlparse(self.path).path != "/api/runs":
                    self._send_json({"error": "not found"}, status=404)
                    return
                payload = self._read_json_body()
                self._send_json(app.create_run(str(payload.get("title", "")), str(payload.get("brief", ""))), status=201)
            except ValueError as exc:
                self._send_json({"error": str(exc)}, status=400)
            except Exception as exc:
                self._send_json({"error": str(exc)}, status=500)

        def log_message(self, format: str, *args: Any) -> None:
            print(f"{self.address_string()} - {format % args}")

        def _read_json_body(self) -> dict[str, Any]:
            length = int(self.headers.get("Content-Length", "0"))
            data = self.rfile.read(length)
            return json.loads(data.decode("utf-8")) if data else {}

        def _serve_static(self, url_path: str) -> None:
            relative = "index.html" if url_path in ["", "/"] else url_path.lstrip("/")
            target = _safe_child(app.config.root, relative)
            if not target.is_file():
                raise FileNotFoundError(relative)
            data = target.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", mimetypes.guess_type(str(target))[0] or "application/octet-stream")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _send_json(self, payload: Any, status: int = 200) -> None:
            data = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _send_text(self, text: str, status: int = 200) -> None:
            data = text.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    return Handler


def _public_roles() -> list[dict[str, str]]:
    return [
        {
            "key": role["key"],
            "role": role["role"],
            "display_role": role["display_role"],
            "label": role["label"],
            "prompt": f"prompts/{role['prompt_file']}",
            "artifact": f"artifacts/{role['artifact']}",
        }
        for role in ROLES
    ]


def _resolve_codex_bin(value: str) -> str:
    found = shutil.which(value) or shutil.which(f"{value}.exe")
    if found:
        return found

    candidates = sorted(Path.home().glob(".vscode/extensions/openai.chatgpt-*/bin/windows-x86_64/codex.exe"), reverse=True)
    return str(candidates[0]) if candidates else value


def _file_manifest(run_dir: Path) -> dict[str, bool]:
    files: dict[str, bool] = {"error": (run_dir / "error.log").is_file()}
    for role in _public_roles():
        files[role["prompt"]] = (run_dir / role["prompt"]).is_file()
        files[role["artifact"]] = (run_dir / role["artifact"]).is_file()
    return files


def _safe_child(root: Path, relative_path: str) -> Path:
    root_resolved = root.resolve()
    target = (root_resolved / relative_path).resolve()
    if root_resolved != target and root_resolved not in target.parents:
        raise ValueError("path escapes allowed directory")
    return target


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _read_optional(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else "(not available yet)"


def _read_last_message(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return ""
    try:
        path.unlink()
    except OSError:
        pass
    return text


def _compact_codex_output(result: subprocess.CompletedProcess[str]) -> str:
    text = "\n".join(part for part in [result.stdout, result.stderr] if part).strip()
    return "\n".join(text.splitlines()[-40:]).strip() if text else ""


def _strip_markdown_fence(response: str) -> str:
    text = response.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _utf8_environment() -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("PYTHONUTF8", "1")
    env.setdefault("PYTHONIOENCODING", "utf-8")
    return env


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Research Report Team local web app.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--codex-bin", default="codex")
    parser.add_argument("--codex-model", default="")
    parser.add_argument("--codex-sandbox", default="read-only")
    parser.add_argument("--job-timeout", type=int, default=1800)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    app = ResearchTeamServer(
        ServerConfig(
            root=root,
            runs_dir=root / "runs",
            codex_bin=_resolve_codex_bin(args.codex_bin),
            codex_model=args.codex_model,
            codex_sandbox=args.codex_sandbox,
            job_timeout=args.job_timeout,
        )
    )
    httpd = ThreadingHTTPServer((args.host, args.port), make_handler(app))
    print(f"Research Report Team running at http://{args.host}:{args.port}", flush=True)
    print(f"Codex binary: {app.config.codex_bin}", flush=True)
    print(f"Codex sandbox: {app.config.codex_sandbox}", flush=True)
    httpd.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
