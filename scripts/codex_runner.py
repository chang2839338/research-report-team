"""Codex CLI runner for role execution."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class CodexConfig:
    codex_bin: str
    codex_model: str
    codex_sandbox: str
    job_timeout: int


class CodexRunner:
    def __init__(self, config: CodexConfig) -> None:
        self.config = config

    def run(self, prompt: str, cwd: Path, last_message_path: Path) -> subprocess.CompletedProcess[str]:
        command = [
            resolve_codex_bin(self.config.codex_bin),
            "exec",
            "--skip-git-repo-check",
            "--sandbox",
            self.config.codex_sandbox,
            "--cd",
            str(cwd),
            "--color",
            "never",
            "--json",
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
                env=utf8_environment(),
            )
        except FileNotFoundError as exc:
            raise FileNotFoundError(f"Codex executable was not found: {command[0]!r}") from exc


def resolve_codex_bin(value: str) -> str:
    found = shutil.which(value) or shutil.which(f"{value}.exe")
    if found:
        return found
    candidates = sorted(Path.home().glob(".vscode/extensions/openai.chatgpt-*/bin/windows-x86_64/codex.exe"), reverse=True)
    return str(candidates[0]) if candidates else value


def utf8_environment() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONLEGACYWINDOWSSTDIO"] = "0"
    return env


def extract_token_usage(output: str) -> dict[str, int]:
    usage: dict[str, int] = {}
    for line in output.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        event_usage = event.get("usage") if event.get("type") == "turn.completed" else None
        if not isinstance(event_usage, dict):
            continue
        usage = {
            key: int(value)
            for key, value in event_usage.items()
            if isinstance(value, (int, float)) and not isinstance(value, bool)
        }
    return usage


def compact_codex_output(result: subprocess.CompletedProcess[str]) -> str:
    text = "\n".join(part for part in [result.stdout, result.stderr] if part).strip()
    return "\n".join(text.splitlines()[-60:]).strip() if text else ""

