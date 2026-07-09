#!/usr/bin/env python3
"""Local web server for running the research-report-team through Codex."""

from __future__ import annotations

import argparse
import json
import mimetypes
import threading
import urllib.parse
from dataclasses import dataclass
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from codex_runner import CodexConfig, CodexRunner, resolve_codex_bin
from contracts import public_roles, split_artifact_sections
from store import RunStore, safe_child
from workflow import WorkflowEngine


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
        self.store = RunStore(config.runs_dir)
        self.runner = CodexRunner(
            CodexConfig(
                codex_bin=config.codex_bin,
                codex_model=config.codex_model,
                codex_sandbox=config.codex_sandbox,
                job_timeout=config.job_timeout,
            )
        )
        self.engine = WorkflowEngine(config.root, self.store, self.runner)
        self._lock = threading.Lock()

    def create_run(self, title: str, brief: str, mode: str = "quality-first") -> dict[str, Any]:
        title = title.strip() or "Untitled report"
        brief = brief.strip()
        if not brief:
            raise ValueError("보고서 내용을 입력하세요.")
        mode = mode.strip() or "quality-first"
        if mode != "quality-first":
            raise ValueError("unsupported mode")

        run_id = self._unique_run_id()
        self.store.create_run(run_id, title, brief, mode)
        threading.Thread(target=self.engine.run_workflow, args=(run_id,), daemon=True).start()
        return self.get_run(run_id)

    def list_runs(self) -> list[dict[str, Any]]:
        return self.store.list_runs()

    def get_run(self, run_id: str) -> dict[str, Any]:
        return self.store.get_run(run_id)

    def read_file(self, run_id: str, relative_path: str) -> str:
        return self.store.read_file(run_id, relative_path)

    def _unique_run_id(self) -> str:
        base = datetime.now().strftime("%Y%m%d_%H%M%S")
        with self._lock:
            run_id = base
            suffix = 1
            while (self.config.runs_dir / run_id).exists():
                suffix += 1
                run_id = f"{base}_{suffix:02d}"
            return run_id

    # Test hooks retained for focused harness tests.
    def _run_role(self, run_dir: Path, task: dict[str, Any], role: Any) -> dict[str, int]:
        return self.engine.run_role(run_dir, task, role)


def make_handler(app: ResearchTeamServer) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        server_version = "ResearchTeamServer/2.0"

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
                run = app.create_run(
                    str(payload.get("title", "")),
                    str(payload.get("brief", "")),
                    str(payload.get("mode", "quality-first")),
                )
                self._send_json(run, status=201)
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
            target = safe_child(app.config.root, relative)
            if not target.is_file():
                raise FileNotFoundError(relative)
            data = target.read_bytes()
            content_type = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
            if content_type.startswith("text/") or content_type in ["application/javascript"]:
                content_type = f"{content_type}; charset=utf-8"
            self.send_response(200)
            self.send_header("Content-Type", content_type)
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


def _public_roles() -> list[dict[str, Any]]:
    return public_roles()


def _split_artifact_sections(response: str, required_names: list[str]) -> dict[str, str]:
    return split_artifact_sections(response, required_names)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


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
    codex_bin = resolve_codex_bin(args.codex_bin)
    app = ResearchTeamServer(
        ServerConfig(
            root=root,
            runs_dir=root / "runs",
            codex_bin=codex_bin,
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

