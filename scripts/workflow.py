"""Quality-first workflow orchestration."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
from typing import Any

from codex_runner import CodexRunner, compact_codex_output, extract_token_usage
from contracts import RoleSpec, WORKFLOW, review_requires_revision, split_artifact_sections
from docx_writer import write_docx_from_markdown
from store import RunStore, now_iso


class WorkflowEngine:
    def __init__(self, root: Path, store: RunStore, runner: CodexRunner) -> None:
        self.root = root
        self.store = store
        self.runner = runner

    def run_workflow(self, run_id: str) -> None:
        run_dir = self.store.run_dir(run_id)
        task = self.store.read_json(run_dir / "task.json")
        try:
            for role in WORKFLOW:
                status = self.store.read_json(run_dir / "status.json")
                if role.conditional == "review_requires_revision" and not _needs_revision(run_dir):
                    continue
                if role.key == "final_verifier" and _needs_revision(run_dir):
                    self.store.update_status(run_dir, state="needs_revision")

                self.store.update_status(run_dir, state="running", current_role=role.key, failed_role="", error="")
                usage = self.run_role(run_dir, task, role)
                self.store.append_agent_run(run_dir, _agent_entry(role), role.artifact_paths, usage)

                if role.key == "reviewer":
                    self._record_review_decision(run_dir)

            self.publish(run_dir, task)
        except Exception as exc:
            detail = _format_exception(exc)
            self.store.atomic_write_text(run_dir / "error.log", detail)
            current = self.store.read_json(run_dir / "status.json").get("current_role", "")
            self.store.update_status(run_dir, state="failed", failed_role=current, error=detail)
            self.store.append_event(run_dir, {"type": "workflow.failed", "role": current, "error": detail})

    def run_role(self, run_dir: Path, task: dict[str, Any], role: RoleSpec) -> dict[str, int]:
        prompt = self.build_execution_prompt(role, task, run_dir)
        prompt_path = run_dir / "prompts" / role.prompt_file
        last_message_path = run_dir / "artifacts" / f"{Path(role.primary_artifact).stem}.last.md"
        self.store.atomic_write_text(prompt_path, prompt)

        result = self.runner.run(prompt, run_dir, last_message_path)
        self._write_role_logs(run_dir, role, result)
        usage = extract_token_usage(result.stdout)
        reply = _strip_markdown_fence(_read_last_message(last_message_path))

        if result.returncode != 0:
            detail = compact_codex_output(result)
            if reply:
                detail = f"{detail}\n\nLast message:\n{reply}".strip()
            raise RuntimeError(f"{role.role} Codex exited {result.returncode}: {detail}")
        if not reply.strip():
            raise RuntimeError(f"{role.role} returned an empty artifact")

        if len(role.artifacts) > 1:
            sections = split_artifact_sections(reply, role.artifact_paths)
            for name, content in sections.items():
                self.store.atomic_write_text(run_dir / "artifacts" / name, content)
        else:
            self.store.atomic_write_text(run_dir / "artifacts" / role.primary_artifact, reply)

        self.store.append_event(
            run_dir,
            {
                "type": "role.completed",
                "role": role.key,
                "artifacts": [f"artifacts/{path}" for path in role.artifact_paths],
                "usage": usage,
            },
        )
        return usage

    def build_execution_prompt(self, role: RoleSpec, task: dict[str, Any], run_dir: Path) -> str:
        role_prompt = _read_optional(self.root / "prompts" / role.prompt)
        context_parts = [
            "# Run Context",
            f"- Report title: {task['title']}",
            f"- User request: {task['brief']}",
            f"- Workflow mode: {task.get('mode', 'quality-first')}",
            f"- Current role: {role.role}",
            f"- Current step: {role.label}",
            f"- Goal: {role.goal}",
            "- OpenAI API direct calls are forbidden. Use only the current Codex execution context.",
            "- Output language: Korean unless the user request clearly requires another language.",
            "- Output only the Markdown body for the target artifact or artifact sections.",
            "- Do not wrap the answer in code fences.",
            "- Do not edit local files; the server will save your final answer.",
        ]
        if len(role.artifacts) > 1:
            context_parts.extend(
                [
                    "- Return multiple artifact sections in one Markdown response.",
                    "- Start each artifact section with the exact marker shown below.",
                    "- Do not omit, rename, reorder, duplicate, translate, or wrap artifact markers.",
                    *[f"  - <!-- artifact: {artifact.path} -->" for artifact in role.artifacts],
                ]
            )
        else:
            context_parts.append(f"- Output artifact: artifacts/{role.primary_artifact}")

        context_parts.extend(["", "# Role Prompt", role_prompt])

        for artifact in role.inputs:
            context_parts.extend(["", f"# Input: artifacts/{artifact}", _read_optional(run_dir / "artifacts" / artifact)])

        for extra in role.extra_inputs:
            context_parts.extend(["", f"# Reference: {extra}", _read_optional(self.root / extra)])

        if role.key == "publisher":
            context_parts.extend(
                [
                    "",
                    "# Publisher Instruction",
                    "Produce artifacts/08_final.md as the final Markdown report only. Use 06_revision.md if it exists and is substantive; otherwise use 04_draft.md. "
                    "Apply Final Verifier notes. The server will create 08_final.docx and 08_final_manifest.json after this role completes.",
                ]
            )
        return "\n".join(context_parts).strip() + "\n"

    def publish(self, run_dir: Path, task: dict[str, Any]) -> None:
        self.store.update_status(run_dir, state="publishing", current_role="publisher")
        final_md = run_dir / "artifacts" / "08_final.md"
        final_docx = run_dir / "artifacts" / "08_final.docx"
        final_manifest = run_dir / "artifacts" / "08_final_manifest.json"
        if not final_md.is_file() or not final_md.read_text(encoding="utf-8").strip():
            raise RuntimeError("final Markdown artifact is missing")

        docx_status = "generated"
        try:
            write_docx_from_markdown(final_md, final_docx, task["title"])
        except Exception as exc:
            docx_status = "failed"
            self.store.append_event(run_dir, {"type": "docx.failed", "error": str(exc)})

        manifest = {
            "published_at": now_iso(),
            "title": task["title"],
            "final_markdown": "artifacts/08_final.md",
            "final_docx": "artifacts/08_final.docx" if final_docx.is_file() else "",
            "docx_status": docx_status,
            "quality_gate": self.store.read_json(run_dir / "status.json").get("quality_gate", {}),
            "revision_count": self.store.read_json(run_dir / "status.json").get("revision_count", 0),
        }
        self.store.write_json(final_manifest, manifest)
        final_complete = final_docx.is_file() and final_manifest.is_file()
        state = "completed" if final_complete else "completed_markdown_only"
        self.store.update_status(
            run_dir,
            state=state,
            current_role="",
            docx_status=docx_status if final_docx.is_file() else "failed",
            error="",
        )

    def _record_review_decision(self, run_dir: Path) -> None:
        review = _read_optional(run_dir / "artifacts" / "05_review.md")
        needs_revision = review_requires_revision(review)
        status = self.store.read_json(run_dir / "status.json")
        revision_count = status.get("revision_count", 0) + (1 if needs_revision else 0)
        decision = "needs_revision" if needs_revision else "approved"
        self.store.update_status(
            run_dir,
            state="needs_revision" if needs_revision else "running",
            revision_count=revision_count,
            quality_gate={"decision": decision, "review_artifact": "artifacts/05_review.md"},
        )

    def _write_role_logs(
        self,
        run_dir: Path,
        role: RoleSpec,
        result: subprocess.CompletedProcess[str],
    ) -> None:
        log_dir = run_dir / "logs"
        self.store.atomic_write_text(log_dir / f"{role.key}.stdout.log", result.stdout or "")
        self.store.atomic_write_text(log_dir / f"{role.key}.stderr.log", result.stderr or "")
        for line in (result.stdout or "").splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            self.store.append_event(run_dir, {"type": "codex.event", "role": role.key, "event": event})


def _needs_revision(run_dir: Path) -> bool:
    review_path = run_dir / "artifacts" / "05_review.md"
    return review_path.is_file() and review_requires_revision(review_path.read_text(encoding="utf-8"))


def _agent_entry(role: RoleSpec) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "key": role.key,
        "role": role.role,
        "label": role.label,
        "artifact": f"artifacts/{role.primary_artifact}",
        "artifacts": [f"artifacts/{path}" for path in role.artifact_paths],
        "prompt": f"prompts/{role.prompt_file}",
        "status": "completed",
        "completed_at": now_iso(),
    }
    return entry


def _read_optional(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else "(not available yet)"


def _read_last_message(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8").strip()
    except OSError:
        return ""
    try:
        path.unlink()
    except OSError:
        pass
    return text


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


def _format_exception(exc: Exception) -> str:
    return f"{type(exc).__name__}: {exc}"
