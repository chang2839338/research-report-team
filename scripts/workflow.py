"""Quality-first workflow orchestration."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any

from codex_runner import CodexRunner, compact_codex_output, extract_token_usage
from contracts import (
    SYSTEM,
    RoleSpec,
    WORKFLOW,
    analysis_gate_decision,
    evidence_gate_decision,
    final_gate_decision,
    read_json_artifact,
    review_requires_revision,
    review_decision,
    split_artifact_sections,
    task_contract_status,
)
from docx_writer import write_docx_from_markdown
from store import RunStore, now_iso


BLOCKED_STATES = {"blocked", "failed", "cancelled", "needs_clarification"}


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
                if status.get("state") in BLOCKED_STATES:
                    return
                if role.conditional == "review_requires_revision" and not _needs_revision(run_dir):
                    continue

                if role.execution == SYSTEM:
                    self._run_system_role(run_dir, task, role)
                    continue

                role_started_at = now_iso()
                self.store.update_status(
                    run_dir,
                    state="running",
                    current_role=role.key,
                    current_role_started_at=role_started_at,
                    failed_role="",
                    error="",
                )
                usage = self.run_role(run_dir, task, role)
                self.store.append_agent_run(run_dir, _agent_entry(role, role_started_at), role.artifact_paths, usage)
                if self._apply_role_gate(run_dir, role):
                    return
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
            try:
                sections = split_artifact_sections(reply, role.artifact_paths)
            except RuntimeError as exc:
                sections, repair_usage = self._repair_artifact_sections(run_dir, role, reply, str(exc))
                usage = _merge_usage(usage, repair_usage)
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
            "- If a target artifact ends in .json, that artifact section must contain valid JSON only.",
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

        if role.key == "final_verifier":
            context_parts.append(f"- Final candidate artifact: artifacts/{_select_candidate_name(run_dir)}")

        context_parts.extend(["", "# Role Prompt", role_prompt])

        for artifact in role.inputs:
            context_parts.extend(["", f"# Input: artifacts/{artifact}", _read_optional(run_dir / "artifacts" / artifact)])

        for extra in role.extra_inputs:
            context_parts.extend(["", f"# Reference: {extra}", _read_optional(self.root / extra)])

        return "\n".join(context_parts).strip() + "\n"

    def publish(self, run_dir: Path, task: dict[str, Any], role: RoleSpec) -> None:
        self.store.update_status(run_dir, state="publishing", current_role=role.key)
        final_gate = read_json_artifact(run_dir, "07_final_verification.json")
        decision = final_gate_decision(final_gate)
        if decision == "blocked" or final_gate.get("block_publish") is True:
            self.store.update_status(
                run_dir,
                state="blocked",
                current_role="",
                final_gate=final_gate,
                error="Final Verifier blocked publication.",
            )
            return

        candidate_name = _verified_candidate_name(run_dir, final_gate)
        candidate = run_dir / "artifacts" / candidate_name
        candidate_text = _read_candidate(candidate)
        final_md = run_dir / "artifacts" / "08_final.md"
        final_docx = run_dir / "artifacts" / "08_final.docx"
        final_manifest = run_dir / "artifacts" / "08_final_manifest.json"

        final_text = _normalize_final_markdown(candidate_text)
        self.store.atomic_write_text(final_md, final_text)

        docx_status = "generated"
        try:
            write_docx_from_markdown(final_md, final_docx, task["title"])
        except Exception as exc:
            docx_status = "failed"
            self.store.append_event(run_dir, {"type": "docx.failed", "error": str(exc)})

        status = self.store.read_json(run_dir / "status.json")
        manifest = {
            "published_at": now_iso(),
            "title": task["title"],
            "selected_source_artifact": f"artifacts/{candidate_name}",
            "selected_source_sha256": _sha256_text(candidate_text),
            "final_markdown": "artifacts/08_final.md",
            "final_markdown_sha256": _sha256_text(final_text),
            "final_docx": "artifacts/08_final.docx" if final_docx.is_file() else "",
            "final_manifest": "artifacts/08_final_manifest.json",
            "docx_status": docx_status,
            "final_gate": final_gate,
            "carry_forward_caveats": final_gate.get("carry_forward_caveats", []),
            "revision_count": status.get("revision_count", 0),
            "markdown_is_auditable_source": True,
        }
        self.store.write_json(final_manifest, manifest)
        final_complete = final_docx.is_file() and final_manifest.is_file()
        state = "completed" if final_complete else "completed_markdown_only"
        self.store.update_status(
            run_dir,
            state=state,
            current_role="",
            selected_final_candidate=f"artifacts/{candidate_name}",
            final_gate=final_gate,
            docx_status=docx_status if final_docx.is_file() else "failed",
            error="",
        )
        self.store.append_event(
            run_dir,
            {
                "type": "system.published",
                "role": role.key,
                "selected_source_artifact": f"artifacts/{candidate_name}",
                "final_markdown": "artifacts/08_final.md",
                "docx_status": docx_status,
            },
        )

    def _apply_role_gate(self, run_dir: Path, role: RoleSpec) -> bool:
        if role.key == "manager":
            contract = read_json_artifact(run_dir, "00_task_contract.json")
            status = task_contract_status(contract)
            self.store.update_status(run_dir, task_contract=contract)
            if status == "needs_user_input":
                self.store.update_status(
                    run_dir,
                    state="needs_clarification",
                    current_role="",
                    pending_user_feedback=True,
                    error="Manager requested clarification before research.",
                )
                return True
            return False

        if role.key == "evidence_auditor":
            gate = read_json_artifact(run_dir, "02_evidence_gate.json")
            decision = evidence_gate_decision(gate)
            self.store.update_status(run_dir, evidence_gate=gate)
            if decision in {"blocked", "incomplete"}:
                self.store.update_status(
                    run_dir,
                    state="blocked",
                    current_role="",
                    error=f"Evidence gate stopped workflow: {decision}",
                )
                return True
            return False

        if role.key == "analyst":
            gate = read_json_artifact(run_dir, "03_analysis_status.json")
            decision = analysis_gate_decision(gate)
            self.store.update_status(run_dir, analysis_gate=gate)
            if decision in {"blocked", "needs_research"}:
                self.store.update_status(
                    run_dir,
                    state="blocked",
                    current_role="",
                    error=f"Analysis gate stopped workflow: {decision}",
                )
                return True
            return False

        if role.key == "reviewer":
            decision = read_json_artifact(run_dir, "05_review_decision.json")
            self._record_review_decision(run_dir, decision)
            return False

        if role.key == "revision_writer":
            self.store.update_status(
                run_dir,
                revision_status={"status": "completed", "artifact": "artifacts/06_revision.md"},
            )
            return False

        if role.key == "final_verifier":
            gate = read_json_artifact(run_dir, "07_final_verification.json")
            decision = final_gate_decision(gate)
            self.store.update_status(run_dir, final_gate=gate)
            if decision == "blocked" or gate.get("block_publish") is True:
                self.store.update_status(
                    run_dir,
                    state="blocked",
                    current_role="",
                    error="Final Verifier blocked publication.",
                )
                return True
            return False

        return False

    def _record_review_decision(self, run_dir: Path, decision: dict[str, Any]) -> None:
        resolved_decision = review_decision(decision)
        needs_revision = review_requires_revision(decision)
        status = self.store.read_json(run_dir / "status.json")
        revision_count = status.get("revision_count", 0) + (1 if needs_revision else 0)
        self.store.update_status(
            run_dir,
            revision_count=revision_count,
            review_gate=decision,
            revision_status={
                "required": needs_revision,
                "decision": resolved_decision,
                "status": "pending" if needs_revision else "not_required",
            },
        )

    def _run_system_role(self, run_dir: Path, task: dict[str, Any], role: RoleSpec) -> None:
        role_started_at = now_iso()
        self.store.update_status(run_dir, current_role_started_at=role_started_at)
        self.publish(run_dir, task, role)
        status = self.store.read_json(run_dir / "status.json")
        if status.get("state") not in BLOCKED_STATES:
            self.store.append_agent_run(run_dir, _agent_entry(role, role_started_at), role.artifact_paths, None)

    def _repair_artifact_sections(
        self,
        run_dir: Path,
        role: RoleSpec,
        reply: str,
        error: str,
    ) -> tuple[dict[str, str], dict[str, int]]:
        last_message_path = run_dir / "artifacts" / f"{Path(role.primary_artifact).stem}.repair.last.md"
        repair_prompt = "\n".join(
            [
                "# Artifact Repair",
                f"The previous {role.role} response did not match the required artifact contract.",
                f"Parser error: {error}",
                "Rewrite the same content into exactly these artifact sections, in this order.",
                "Do not add new facts. Do not wrap the answer in code fences.",
                *[f"- <!-- artifact: {artifact.path} -->" for artifact in role.artifacts],
                "",
                "# Previous Response",
                reply,
            ]
        )
        result = self.runner.run(repair_prompt, run_dir, last_message_path)
        repair_role = RoleSpec(
            key=f"{role.key}_repair",
            role=f"{role.role} Repair",
            display_role=f"{role.display_role} Repair",
            label=f"{role.label} Repair",
            prompt=role.prompt,
            prompt_file=role.prompt_file,
            artifacts=role.artifacts,
            execution=role.execution,
            output_contract=role.output_contract,
        )
        self._write_role_logs(run_dir, repair_role, result)
        repaired = _strip_markdown_fence(_read_last_message(last_message_path))
        if result.returncode != 0:
            raise RuntimeError(f"{role.role} artifact repair failed: {compact_codex_output(result)}")
        sections = split_artifact_sections(repaired, role.artifact_paths)
        usage = extract_token_usage(result.stdout)
        self.store.append_event(
            run_dir,
            {"type": "role.artifact_repaired", "role": role.key, "artifacts": role.artifact_paths},
        )
        return sections, usage

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
    decision = read_json_artifact(run_dir, "05_review_decision.json")
    return bool(decision) and review_requires_revision(decision)


def _select_candidate_name(run_dir: Path) -> str:
    final_gate = read_json_artifact(run_dir, "07_final_verification.json")
    candidate = final_gate.get("candidate_artifact")
    if isinstance(candidate, str) and candidate.startswith("artifacts/"):
        return candidate.removeprefix("artifacts/")
    if _needs_revision(run_dir) and _is_substantive(run_dir / "artifacts" / "06_revision.md"):
        return "06_revision.md"
    return "04_draft.md"


def _verified_candidate_name(run_dir: Path, final_gate: dict[str, Any]) -> str:
    candidate = final_gate.get("candidate_artifact")
    if isinstance(candidate, str) and candidate.startswith("artifacts/"):
        name = candidate.removeprefix("artifacts/")
    else:
        name = _select_candidate_name(run_dir)
    if name not in {"04_draft.md", "06_revision.md"}:
        raise RuntimeError(f"invalid final candidate artifact: {name}")
    return name


def _read_candidate(path: Path) -> str:
    if not path.is_file():
        raise RuntimeError(f"final candidate is missing: {path.name}")
    text = path.read_text(encoding="utf-8").strip()
    if not text or text.upper() == "TBD":
        raise RuntimeError(f"final candidate is empty or placeholder: {path.name}")
    return text + "\n"


def _is_substantive(path: Path) -> bool:
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8").strip()
    return bool(text and text.upper() != "TBD" and "TBD" not in text[:80])


def _normalize_final_markdown(text: str) -> str:
    return _strip_markdown_fence(text).strip() + "\n"


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _agent_entry(role: RoleSpec, started_at: str) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "key": role.key,
        "role": role.role,
        "label": role.label,
        "artifact": f"artifacts/{role.primary_artifact}",
        "artifacts": [f"artifacts/{path}" for path in role.artifact_paths],
        "prompt": f"prompts/{role.prompt_file}" if role.prompt_file else "",
        "status": "completed",
        "started_at": started_at,
        "completed_at": now_iso(),
        "execution": role.execution,
    }
    return entry


def _merge_usage(left: dict[str, int], right: dict[str, int]) -> dict[str, int]:
    merged = dict(left)
    for key, value in right.items():
        merged[key] = merged.get(key, 0) + value
    return merged


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
