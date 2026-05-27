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


MAX_GATE_ATTEMPTS = 2
STOP_STATES = {"failed", "cancelled", "needs_clarification"}
RECOVERABLE_GATES = {"evidence", "analysis", "review", "final"}


class WorkflowEngine:
    def __init__(self, root: Path, store: RunStore, runner: CodexRunner) -> None:
        self.root = root
        self.store = store
        self.runner = runner

    def run_workflow(self, run_id: str) -> None:
        run_dir = self.store.run_dir(run_id)
        task = self.store.read_json(run_dir / "task.json")
        try:
            self._run_role_attempt(run_dir, task, _role("manager"))
            if self._handle_manager_gate(run_dir):
                return

            self._run_role_attempt(run_dir, task, _role("researcher"))

            self._run_role_attempt(run_dir, task, _role("evidence_auditor"))
            self._recover_evidence_gate(run_dir, task)

            self._run_role_attempt(run_dir, task, _role("analyst"))
            self._recover_analysis_gate(run_dir, task)

            self._run_role_attempt(run_dir, task, _role("writer"))

            self._run_role_attempt(run_dir, task, _role("reviewer"))
            self._recover_review_gate(run_dir, task)

            self._run_role_attempt(run_dir, task, _role("final_verifier"))
            self._recover_final_gate(run_dir, task)

            self._run_system_role(run_dir, task, _role("publisher"))
        except Exception as exc:
            detail = _format_exception(exc)
            self.store.atomic_write_text(run_dir / "error.log", detail)
            current = self.store.read_json(run_dir / "status.json").get("current_role", "")
            self.store.update_status(run_dir, state="failed", failed_role=current, error=detail)
            self.store.append_event(run_dir, {"type": "workflow.failed", "role": current, "error": detail})

    def run_role(
        self,
        run_dir: Path,
        task: dict[str, Any],
        role: RoleSpec,
        recovery_context: dict[str, Any] | None = None,
    ) -> dict[str, int]:
        prompt = self.build_execution_prompt(role, task, run_dir, recovery_context)
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

    def build_execution_prompt(
        self,
        role: RoleSpec,
        task: dict[str, Any],
        run_dir: Path,
        recovery_context: dict[str, Any] | None = None,
    ) -> str:
        role_prompt = _read_optional(self.root / "prompts" / role.prompt)
        status = self.store.read_json(run_dir / "status.json")
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
        unresolved = status.get("unresolved_gate_issues", [])
        context_parts.extend(
            [
                "",
                "# Carry-Forward Gate Issues",
                json.dumps(unresolved, ensure_ascii=False, indent=2) if unresolved else "[]",
                "- If this list is non-empty, treat the items as unresolved limitations that must be carried into analysis, caveats, trace notes, review checks, final verification, and the final report.",
                "- Do not hide unresolved gate issues. Writer-facing outputs must include a limitations/caveats section when unresolved issues exist.",
            ]
        )
        if recovery_context:
            context_parts.extend(
                [
                    "",
                    "# Remediation Context",
                    json.dumps(recovery_context, ensure_ascii=False, indent=2),
                    "- This is a targeted remediation run. Preserve valid prior content and update only what is needed to address the listed gate issues.",
                    "- Return the full latest artifact set for this role, not a patch or partial diff.",
                ]
            )
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
        unresolved = self.store.read_json(run_dir / "status.json").get("unresolved_gate_issues", [])
        conditional_publish = bool(unresolved)
        if (decision == "blocked" or final_gate.get("block_publish") is True) and not conditional_publish:
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
            "publication_status": "completed_with_unresolved_issues" if conditional_publish else "completed",
            "unresolved_gate_issues": unresolved,
            "markdown_is_auditable_source": True,
        }
        self.store.write_json(final_manifest, manifest)
        final_complete = final_docx.is_file() and final_manifest.is_file()
        state = "completed_with_unresolved_issues" if conditional_publish and final_complete else "completed" if final_complete else "completed_markdown_only"
        self.store.update_status(
            run_dir,
            state=state,
            current_role="",
            selected_final_candidate=f"artifacts/{candidate_name}",
            final_gate=final_gate,
            docx_status=docx_status if final_docx.is_file() else "failed",
            error="Completed with unresolved gate issues." if conditional_publish else "",
        )
        self.store.append_event(
            run_dir,
            {
                "type": "system.published",
                "role": role.key,
                "selected_source_artifact": f"artifacts/{candidate_name}",
                "final_markdown": "artifacts/08_final.md",
                "docx_status": docx_status,
                "publication_status": manifest["publication_status"],
            },
        )

    def _run_role_attempt(
        self,
        run_dir: Path,
        task: dict[str, Any],
        role: RoleSpec,
        run_kind: str = "normal",
        trigger_gate: str = "",
        loop_id: str = "",
        recovery_context: dict[str, Any] | None = None,
        continued_after_exhaustion: bool = False,
    ) -> None:
        status = self.store.read_json(run_dir / "status.json")
        if status.get("state") in STOP_STATES:
            return
        role_started_at = now_iso()
        attempt = _next_role_attempt(status, role.key)
        state = "remediating" if run_kind in {"remediation", "gate_retry"} else "running"
        self.store.update_status(
            run_dir,
            state=state,
            current_role=role.key,
            current_role_started_at=role_started_at,
            failed_role="",
            error="",
        )
        usage = self.run_role(run_dir, task, role, recovery_context)
        entry = _agent_entry(role, role_started_at)
        entry.update(
            {
                "attempt": attempt,
                "run_kind": run_kind,
                "trigger_gate": trigger_gate,
                "loop_id": loop_id,
                "continued_after_exhaustion": continued_after_exhaustion,
            }
        )
        self.store.append_agent_run(run_dir, entry, role.artifact_paths, usage)

    def _handle_manager_gate(self, run_dir: Path) -> bool:
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

    def _recover_evidence_gate(self, run_dir: Path, task: dict[str, Any]) -> None:
        gate = read_json_artifact(run_dir, "02_evidence_gate.json")
        decision = evidence_gate_decision(gate)
        self.store.update_status(run_dir, evidence_gate=gate)
        if decision not in {"blocked", "incomplete"}:
            return

        last_gate = gate
        for attempt in _gate_attempt_range(run_dir, "evidence", self.store):
            loop_id = self._record_loop_iteration(run_dir, "evidence", attempt, "researcher", "evidence_auditor")
            context = _recovery_context("evidence", attempt, last_gate, "Researcher must fill only the evidence gaps that made the Evidence Gate fail.")
            self._run_role_attempt(run_dir, task, _role("researcher"), "remediation", "evidence", loop_id, context)
            self._run_role_attempt(run_dir, task, _role("evidence_auditor"), "gate_retry", "evidence", loop_id, context)
            last_gate = read_json_artifact(run_dir, "02_evidence_gate.json")
            decision = evidence_gate_decision(last_gate)
            self.store.update_status(run_dir, evidence_gate=last_gate)
            if decision not in {"blocked", "incomplete"}:
                return

        self._continue_with_unresolved_gate(
            run_dir,
            "evidence",
            decision,
            MAX_GATE_ATTEMPTS,
            "evidence_auditor",
            last_gate,
            "Downstream roles must treat failed or incomplete evidence as unresolved caveats and separate observed facts from estimates.",
        )

    def _recover_analysis_gate(self, run_dir: Path, task: dict[str, Any]) -> None:
        gate = read_json_artifact(run_dir, "03_analysis_status.json")
        decision = analysis_gate_decision(gate)
        self.store.update_status(run_dir, analysis_gate=gate)
        if decision not in {"blocked", "needs_research"}:
            return

        last_gate = gate
        for attempt in _gate_attempt_range(run_dir, "analysis", self.store):
            loop_id = self._record_loop_iteration(run_dir, "analysis", attempt, "researcher", "analyst")
            context = _recovery_context("analysis", attempt, last_gate, "Researcher must fill analysis-blocking gaps; Analyst must revise the full analysis using the updated evidence.")
            self._run_role_attempt(run_dir, task, _role("researcher"), "remediation", "analysis", loop_id, context)
            self._run_role_attempt(run_dir, task, _role("evidence_auditor"), "gate_retry", "analysis", loop_id, context)
            self._recover_evidence_gate(run_dir, task)
            self._run_role_attempt(run_dir, task, _role("analyst"), "gate_retry", "analysis", loop_id, context)
            last_gate = read_json_artifact(run_dir, "03_analysis_status.json")
            decision = analysis_gate_decision(last_gate)
            self.store.update_status(run_dir, analysis_gate=last_gate)
            if decision not in {"blocked", "needs_research"}:
                return

        self._continue_with_unresolved_gate(
            run_dir,
            "analysis",
            decision,
            MAX_GATE_ATTEMPTS,
            "analyst",
            last_gate,
            "Writer and Reviewer must label the affected analysis as conditional and preserve the analysis caveats.",
        )

    def _recover_review_gate(self, run_dir: Path, task: dict[str, Any]) -> None:
        decision_payload = read_json_artifact(run_dir, "05_review_decision.json")
        self._record_review_decision(run_dir, decision_payload)
        if not review_requires_revision(decision_payload):
            return

        last_decision = decision_payload
        for attempt in _gate_attempt_range(run_dir, "review", self.store):
            loop_id = self._record_loop_iteration(run_dir, "review", attempt, "revision_writer", "reviewer")
            context = _recovery_context("review", attempt, last_decision, "Revision Writer must apply only required review revisions; Reviewer must re-check the revised candidate.")
            self._run_role_attempt(run_dir, task, _role("revision_writer"), "remediation", "review", loop_id, context)
            self.store.update_status(run_dir, revision_status={"status": "completed", "artifact": "artifacts/06_revision.md"})
            self._run_role_attempt(run_dir, task, _role("reviewer"), "gate_retry", "review", loop_id, context)
            last_decision = read_json_artifact(run_dir, "05_review_decision.json")
            self._record_review_decision(run_dir, last_decision)
            if not review_requires_revision(last_decision):
                return

        self._continue_with_unresolved_gate(
            run_dir,
            "review",
            review_decision(last_decision),
            MAX_GATE_ATTEMPTS,
            "reviewer",
            last_decision,
            "Final Verifier and Publisher must carry unresolved review revisions as limitations in the final report.",
        )

    def _recover_final_gate(self, run_dir: Path, task: dict[str, Any]) -> None:
        gate = read_json_artifact(run_dir, "07_final_verification.json")
        decision = final_gate_decision(gate)
        self.store.update_status(run_dir, final_gate=gate)
        if decision != "blocked" and gate.get("block_publish") is not True:
            return

        last_gate = gate
        for attempt in _gate_attempt_range(run_dir, "final", self.store):
            loop_id = self._record_loop_iteration(run_dir, "final", attempt, "revision_writer", "final_verifier")
            context = _recovery_context("final", attempt, last_gate, "Revision Writer must patch final-verification blockers using only existing evidence and visible caveats.")
            self._run_role_attempt(run_dir, task, _role("revision_writer"), "remediation", "final", loop_id, context)
            self.store.update_status(run_dir, revision_status={"status": "completed", "artifact": "artifacts/06_revision.md"})
            self._run_role_attempt(run_dir, task, _role("final_verifier"), "gate_retry", "final", loop_id, context)
            last_gate = read_json_artifact(run_dir, "07_final_verification.json")
            decision = final_gate_decision(last_gate)
            self.store.update_status(run_dir, final_gate=last_gate)
            if decision != "blocked" and last_gate.get("block_publish") is not True:
                return

        self._continue_with_unresolved_gate(
            run_dir,
            "final",
            decision,
            MAX_GATE_ATTEMPTS,
            "final_verifier",
            last_gate,
            "Publisher must issue a conditional final report and include unresolved final verification blockers.",
        )

    def _record_loop_iteration(
        self,
        run_dir: Path,
        gate: str,
        attempt: int,
        remediate_role: str,
        gate_role: str,
    ) -> str:
        loop_id = f"{gate}-{attempt}"
        status = self.store.read_json(run_dir / "status.json")
        loop_state = status.get("loop_state", {})
        retry_counts = dict(loop_state.get("retry_counts", {}))
        retry_counts[gate] = attempt
        iterations = [
            *loop_state.get("iterations", []),
            {
                "loop_id": loop_id,
                "gate": gate,
                "attempt": attempt,
                "remediate_role": remediate_role,
                "gate_role": gate_role,
                "started_at": now_iso(),
            },
        ]
        loop_state.update(
            {
                "max_attempts_per_gate": MAX_GATE_ATTEMPTS,
                "retry_counts": retry_counts,
                "iterations": iterations,
            }
        )
        self.store.update_status(run_dir, state="remediating", loop_state=loop_state)
        self.store.append_event(run_dir, {"type": "gate.remediation_started", "gate": gate, "attempt": attempt, "loop_id": loop_id})
        return loop_id

    def _continue_with_unresolved_gate(
        self,
        run_dir: Path,
        gate: str,
        decision: str,
        attempts: int,
        source_role: str,
        payload: dict[str, Any],
        downstream_instruction: str,
    ) -> None:
        status = self.store.read_json(run_dir / "status.json")
        if any(issue.get("gate") == gate for issue in status.get("unresolved_gate_issues", [])):
            return
        unresolved = [*status.get("unresolved_gate_issues", [])]
        issue = {
            "gate": gate,
            "decision": decision,
            "attempts": attempts,
            "source_role": source_role,
            "blocking_issues": _extract_gate_issues(payload),
            "continued_at": now_iso(),
            "downstream_instruction": downstream_instruction,
            "gate_exhausted": {"continued": True},
        }
        unresolved.append(issue)
        self.store.update_status(
            run_dir,
            state="continuing_with_issues",
            current_role="",
            unresolved_gate_issues=unresolved,
            error=f"Continuing with unresolved {gate} gate issues.",
        )
        self.store.append_event(run_dir, {"type": "gate.exhausted_continued", **issue})

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
        if status.get("state") not in {*STOP_STATES, "blocked"}:
            entry = _agent_entry(role, role_started_at)
            entry.update(
                {
                    "attempt": _next_role_attempt(status, role.key),
                    "run_kind": "system",
                    "trigger_gate": "",
                    "loop_id": "",
                    "continued_after_exhaustion": bool(status.get("unresolved_gate_issues")),
                }
            )
            self.store.append_agent_run(run_dir, entry, role.artifact_paths, None)

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
        status = self.store.read_json(run_dir / "status.json")
        attempt = _next_role_attempt(status, role.key)
        self.store.atomic_write_text(log_dir / f"{role.key}.stdout.log", result.stdout or "")
        self.store.atomic_write_text(log_dir / f"{role.key}.stderr.log", result.stderr or "")
        self.store.atomic_write_text(log_dir / f"{role.key}.{attempt}.stdout.log", result.stdout or "")
        self.store.atomic_write_text(log_dir / f"{role.key}.{attempt}.stderr.log", result.stderr or "")
        for line in (result.stdout or "").splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            self.store.append_event(run_dir, {"type": "codex.event", "role": role.key, "event": event})


def _role(key: str) -> RoleSpec:
    for role in WORKFLOW:
        if role.key == key:
            return role
    raise RuntimeError(f"unknown role: {key}")


def _next_role_attempt(status: dict[str, Any], role_key: str) -> int:
    return 1 + sum(1 for run in status.get("agent_runs", []) if run.get("key") == role_key)


def _gate_attempt_range(run_dir: Path, gate: str, store: RunStore) -> range:
    status = store.read_json(run_dir / "status.json")
    current = int(status.get("loop_state", {}).get("retry_counts", {}).get(gate, 0) or 0)
    return range(current + 1, MAX_GATE_ATTEMPTS + 1)


def _recovery_context(gate: str, attempt: int, payload: dict[str, Any], instruction: str) -> dict[str, Any]:
    return {
        "gate": gate,
        "attempt": attempt,
        "max_attempts": MAX_GATE_ATTEMPTS,
        "gate_payload": payload,
        "targeted_instruction": instruction,
    }


def _extract_gate_issues(payload: dict[str, Any]) -> list[Any]:
    for key in [
        "blocking_issues",
        "blocked_reasons",
        "required_revisions",
        "unresolved_required_revisions",
        "unsupported_or_new_claims",
        "missing_required_caveats",
    ]:
        value = payload.get(key)
        if value:
            return value if isinstance(value, list) else [value]
    return [payload] if payload else []


def _needs_revision(run_dir: Path) -> bool:
    decision = read_json_artifact(run_dir, "05_review_decision.json")
    return bool(decision) and review_requires_revision(decision)


def _select_candidate_name(run_dir: Path) -> str:
    final_gate = read_json_artifact(run_dir, "07_final_verification.json")
    candidate = final_gate.get("candidate_artifact")
    if isinstance(candidate, str) and candidate.startswith("artifacts/"):
        return candidate.removeprefix("artifacts/")
    if _is_substantive(run_dir / "artifacts" / "06_revision.md"):
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
