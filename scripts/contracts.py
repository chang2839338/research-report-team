"""Workflow and artifact contracts for the research report team."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


MARKER_PREFIX = "<!-- artifact:"
MARKER_SUFFIX = "-->"

CODEX = "codex"
SYSTEM = "system"


@dataclass(frozen=True)
class ArtifactSpec:
    path: str
    label: str
    required: bool = True
    template: str = ""


@dataclass(frozen=True)
class RoleSpec:
    key: str
    role: str
    display_role: str
    label: str
    prompt: str
    prompt_file: str
    artifacts: tuple[ArtifactSpec, ...]
    inputs: tuple[str, ...] = ()
    extra_inputs: tuple[str, ...] = ()
    goal: str = ""
    conditional: str = "always"
    max_revisions: int = 1
    execution: str = CODEX
    output_contract: str = "single_markdown"

    @property
    def primary_artifact(self) -> str:
        return self.artifacts[0].path

    @property
    def artifact_paths(self) -> list[str]:
        return [artifact.path for artifact in self.artifacts]


DEFAULT_ARTIFACT_TEMPLATES: dict[str, str] = {
    "00_task_contract.json": "{}\n",
    "00_task_brief.md": "# Task Brief\n\nTBD\n",
    "01_research.md": "# Research Memo\n\nTBD\n",
    "01_sources.md": "# Source Ledger\n\nTBD\n",
    "01_claims.md": "# Claim Evidence Table\n\nTBD\n",
    "01_gaps.md": "# Research Gaps And Risks\n\nTBD\n",
    "01_numeric_assumptions.md": "# Numeric Assumptions Ledger\n\nTBD\n",
    "01_source_provenance.md": "# Source Provenance\n\nTBD\n",
    "02_evidence_gate.json": "{}\n",
    "02_evidence_audit.md": "# Evidence Audit\n\nTBD\n",
    "03a_decision_frame.md": "# Decision Frame\n\nTBD\n",
    "03b_option_evaluation.md": "# Option Evaluation\n\nTBD\n",
    "03c_scenarios_and_recommendation.md": "# Scenarios And Recommendation\n\nTBD\n",
    "03_analysis.md": "# Analysis Rollup\n\nTBD\n",
    "03_analysis_status.json": "{}\n",
    "04_draft.md": "# Draft\n\nTBD\n",
    "04_writer_trace.md": "# Writer Trace\n\nTBD\n",
    "05_review_decision.json": "{}\n",
    "05_review.md": "# Review\n\nTBD\n",
    "05_claim_audit.md": "# Claim Audit\n\nTBD\n",
    "06_revision.md": "# Revision\n\nTBD\n",
    "06_revision_trace.md": "# Revision Trace\n\nTBD\n",
    "07_final_verification.json": "{}\n",
    "07_final_verification.md": "# Final Verification\n\nTBD\n",
    "08_final.md": "# Final Report\n\nTBD\n",
    "08_final_manifest.json": "{}\n",
}


WORKFLOW: tuple[RoleSpec, ...] = (
    RoleSpec(
        key="manager",
        role="Manager",
        display_role="Manager",
        label="Task Contract",
        prompt="manager.md",
        prompt_file="00_manager.md",
        artifacts=(
            ArtifactSpec("00_task_contract.json", "Task Contract"),
            ArtifactSpec("00_task_brief.md", "Task Brief"),
        ),
        goal="Create the intake contract and human task brief that guide every later role.",
        output_contract="multi_artifact",
    ),
    RoleSpec(
        key="researcher",
        role="Researcher",
        display_role="Researcher",
        label="Research",
        prompt="researcher.md",
        prompt_file="01_researcher.md",
        artifacts=(
            ArtifactSpec("01_research.md", "Research Memo"),
            ArtifactSpec("01_sources.md", "Sources"),
            ArtifactSpec("01_claims.md", "Claims"),
            ArtifactSpec("01_gaps.md", "Gaps"),
            ArtifactSpec("01_numeric_assumptions.md", "Numeric Ledger"),
            ArtifactSpec("01_source_provenance.md", "Provenance"),
        ),
        inputs=("00_task_contract.json", "00_task_brief.md"),
        goal="Extract source-backed evidence, preliminary claim links, numeric assumptions, and provenance.",
        output_contract="multi_artifact",
    ),
    RoleSpec(
        key="evidence_auditor",
        role="Evidence Auditor",
        display_role="Evidence Audit",
        label="Evidence Gate",
        prompt="evidence_auditor.md",
        prompt_file="02_evidence_auditor.md",
        artifacts=(
            ArtifactSpec("02_evidence_gate.json", "Evidence Gate"),
            ArtifactSpec("02_evidence_audit.md", "Evidence Audit"),
        ),
        inputs=(
            "00_task_contract.json",
            "00_task_brief.md",
            "01_research.md",
            "01_sources.md",
            "01_claims.md",
            "01_gaps.md",
            "01_numeric_assumptions.md",
            "01_source_provenance.md",
        ),
        goal="Decide which extracted evidence is usable, caveated, excluded, blocked, or incomplete.",
        output_contract="json_gate_plus_markdown",
    ),
    RoleSpec(
        key="analyst",
        role="Analyst",
        display_role="Analyst",
        label="Analysis",
        prompt="analyst.md",
        prompt_file="03_analyst.md",
        artifacts=(
            ArtifactSpec("03a_decision_frame.md", "Decision Frame"),
            ArtifactSpec("03b_option_evaluation.md", "Option Evaluation"),
            ArtifactSpec("03c_scenarios_and_recommendation.md", "Scenarios"),
            ArtifactSpec("03_analysis.md", "Analysis Rollup"),
            ArtifactSpec("03_analysis_status.json", "Analysis Status"),
        ),
        inputs=(
            "00_task_contract.json",
            "00_task_brief.md",
            "01_research.md",
            "01_claims.md",
            "01_gaps.md",
            "01_numeric_assumptions.md",
            "02_evidence_gate.json",
            "02_evidence_audit.md",
        ),
        goal="Model the decision using audited evidence and produce a Writer-facing analysis rollup.",
        output_contract="multi_artifact",
    ),
    RoleSpec(
        key="writer",
        role="Writer",
        display_role="Writer",
        label="Draft",
        prompt="writer.md",
        prompt_file="04_writer.md",
        artifacts=(
            ArtifactSpec("04_draft.md", "Draft"),
            ArtifactSpec("04_writer_trace.md", "Writer Trace"),
        ),
        inputs=(
            "00_task_contract.json",
            "00_task_brief.md",
            "01_sources.md",
            "01_claims.md",
            "01_gaps.md",
            "01_numeric_assumptions.md",
            "02_evidence_gate.json",
            "02_evidence_audit.md",
            "03_analysis.md",
            "03_analysis_status.json",
        ),
        extra_inputs=("references/output-templates.md",),
        goal="Write the audience-facing draft and map material claims to evidence.",
        output_contract="multi_artifact",
    ),
    RoleSpec(
        key="reviewer",
        role="Reviewer",
        display_role="Reviewer",
        label="Review",
        prompt="reviewer.md",
        prompt_file="05_reviewer.md",
        artifacts=(
            ArtifactSpec("05_review_decision.json", "Review Decision"),
            ArtifactSpec("05_review.md", "Review"),
            ArtifactSpec("05_claim_audit.md", "Claim Audit"),
        ),
        inputs=(
            "00_task_contract.json",
            "00_task_brief.md",
            "01_sources.md",
            "01_claims.md",
            "01_gaps.md",
            "01_numeric_assumptions.md",
            "02_evidence_gate.json",
            "02_evidence_audit.md",
            "03_analysis.md",
            "04_draft.md",
            "04_writer_trace.md",
        ),
        extra_inputs=("references/report-quality-rubric.md",),
        goal="Audit the draft, trace map, and recommendation; produce a structured revision decision.",
        output_contract="json_gate_plus_markdown",
    ),
    RoleSpec(
        key="revision_writer",
        role="Revision Writer",
        display_role="Revision",
        label="Revision",
        prompt="revision_writer.md",
        prompt_file="06_revision_writer.md",
        artifacts=(
            ArtifactSpec("06_revision.md", "Revised Draft"),
            ArtifactSpec("06_revision_trace.md", "Revision Trace"),
        ),
        inputs=(
            "00_task_contract.json",
            "00_task_brief.md",
            "01_sources.md",
            "01_claims.md",
            "01_gaps.md",
            "01_numeric_assumptions.md",
            "02_evidence_gate.json",
            "02_evidence_audit.md",
            "03_analysis.md",
            "04_draft.md",
            "04_writer_trace.md",
            "05_review_decision.json",
            "05_review.md",
            "05_claim_audit.md",
        ),
        goal="Apply only required review revisions and document revision coverage.",
        conditional="review_requires_revision",
        output_contract="multi_artifact",
    ),
    RoleSpec(
        key="final_verifier",
        role="Final Verifier",
        display_role="Final Verify",
        label="Final Verification",
        prompt="final_verifier.md",
        prompt_file="07_final_verifier.md",
        artifacts=(
            ArtifactSpec("07_final_verification.json", "Final Gate"),
            ArtifactSpec("07_final_verification.md", "Final Verification"),
        ),
        inputs=(
            "00_task_contract.json",
            "00_task_brief.md",
            "01_sources.md",
            "01_claims.md",
            "01_gaps.md",
            "01_numeric_assumptions.md",
            "02_evidence_gate.json",
            "02_evidence_audit.md",
            "03_analysis.md",
            "04_draft.md",
            "04_writer_trace.md",
            "05_review_decision.json",
            "05_review.md",
            "05_claim_audit.md",
            "06_revision.md",
            "06_revision_trace.md",
        ),
        extra_inputs=("references/quality-checklist.md",),
        goal="Enforce the final publish gate for the selected candidate artifact.",
        output_contract="json_gate_plus_markdown",
    ),
    RoleSpec(
        key="publisher",
        role="Publisher",
        display_role="Publisher",
        label="Final Report",
        prompt="",
        prompt_file="",
        artifacts=(
            ArtifactSpec("08_final.md", "Final Report"),
            ArtifactSpec("08_final_manifest.json", "Final Manifest"),
        ),
        goal="Deterministically publish the verified candidate. The server creates 08_final.docx.",
        execution=SYSTEM,
        output_contract="system_publish",
    ),
)


def all_artifact_paths() -> list[str]:
    paths: list[str] = []
    for role in WORKFLOW:
        for artifact in role.artifacts:
            if artifact.path not in paths:
                paths.append(artifact.path)
    return [*paths, "08_final.docx"]


def public_roles() -> list[dict[str, Any]]:
    roles: list[dict[str, Any]] = []
    for role in WORKFLOW:
        roles.append(
            {
                "key": role.key,
                "role": role.role,
                "display_role": role.display_role,
                "label": role.label,
                "prompt": f"prompts/{role.prompt_file}" if role.prompt_file else "",
                "artifact": f"artifacts/{role.primary_artifact}",
                "artifacts": [
                    {
                        "path": f"artifacts/{artifact.path}",
                        "label": artifact.label,
                        "required": artifact.required,
                    }
                    for artifact in role.artifacts
                ],
                "conditional": role.conditional,
                "execution": role.execution,
                "output_contract": role.output_contract,
            }
        )
    return roles


def artifact_manifest(run_dir: Path) -> list[dict[str, Any]]:
    manifest = []
    for role in public_roles():
        for artifact in role["artifacts"]:
            path = artifact["path"]
            target = run_dir / path
            manifest.append(
                {
                    "role_key": role["key"],
                    "label": artifact["label"],
                    "path": path,
                    "required": artifact["required"],
                    "exists": target.is_file(),
                    "size": target.stat().st_size if target.is_file() else 0,
                }
            )
    for path, label in [
        ("artifacts/08_final.docx", "Word Report"),
        ("error.log", "Error Log"),
        ("events.ndjson", "Event Log"),
    ]:
        target = run_dir / path
        manifest.append(
            {
                "role_key": "system",
                "label": label,
                "path": path,
                "required": path == "artifacts/08_final.docx",
                "exists": target.is_file(),
                "size": target.stat().st_size if target.is_file() else 0,
            }
        )
    return manifest


def split_artifact_sections(response: str, required_names: list[str]) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current_name = ""
    seen_order: list[str] = []

    for line in response.splitlines():
        stripped = line.strip()
        if stripped.startswith(MARKER_PREFIX) and stripped.endswith(MARKER_SUFFIX):
            current_name = stripped.removeprefix(MARKER_PREFIX).removesuffix(MARKER_SUFFIX).strip()
            if current_name in sections:
                raise RuntimeError(f"duplicate artifact section: {current_name}")
            sections[current_name] = []
            seen_order.append(current_name)
            continue
        if current_name:
            sections[current_name].append(line)

    missing = [name for name in required_names if name not in sections]
    if missing:
        raise RuntimeError(f"required artifact section missing: {', '.join(missing)}")

    unexpected = [name for name in sections if name not in required_names]
    if unexpected:
        raise RuntimeError(f"unexpected artifact section: {', '.join(unexpected)}")

    expected_order = [name for name in required_names if name in sections]
    if seen_order != expected_order:
        raise RuntimeError("artifact sections are out of order")

    parsed = {}
    for name in required_names:
        content = "\n".join(sections[name]).strip()
        if not content:
            raise RuntimeError(f"required artifact section empty: {name}")
        if name.endswith(".json"):
            parse_json_text(content, name)
        parsed[name] = content + "\n"
    return parsed


def parse_json_text(text: str, artifact_name: str = "json artifact") -> dict[str, Any]:
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{artifact_name} is not valid JSON: {exc.msg}") from exc
    if not isinstance(parsed, dict):
        raise RuntimeError(f"{artifact_name} must contain a JSON object")
    return parsed


def read_json_artifact(run_dir: Path, artifact_name: str) -> dict[str, Any]:
    path = run_dir / "artifacts" / artifact_name
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8").strip()
    return parse_json_text(text, artifact_name) if text else {}


def require_enum(value: Any, allowed: set[str], field: str, artifact_name: str) -> str:
    if not isinstance(value, str) or value not in allowed:
        allowed_text = ", ".join(sorted(allowed))
        raise RuntimeError(f"{artifact_name}.{field} must be one of: {allowed_text}")
    return value


def task_contract_status(contract: dict[str, Any]) -> str:
    return require_enum(
        contract.get("workflow_status"),
        {"ready", "needs_user_input"},
        "workflow_status",
        "00_task_contract.json",
    )


def evidence_gate_decision(gate: dict[str, Any]) -> str:
    return require_enum(
        gate.get("decision"),
        {"pass", "pass_with_caveats", "blocked", "incomplete"},
        "decision",
        "02_evidence_gate.json",
    )


def analysis_gate_decision(status: dict[str, Any]) -> str:
    return require_enum(
        status.get("decision"),
        {"ready", "blocked", "needs_research"},
        "decision",
        "03_analysis_status.json",
    )


def review_decision(decision: dict[str, Any]) -> str:
    return require_enum(
        decision.get("decision"),
        {"approved", "targeted_revision", "needs_revision"},
        "decision",
        "05_review_decision.json",
    )


def review_requires_revision(decision: dict[str, Any]) -> bool:
    return review_decision(decision) in {"targeted_revision", "needs_revision"}


def final_gate_decision(gate: dict[str, Any]) -> str:
    return require_enum(
        gate.get("decision"),
        {"ready", "caveated", "blocked"},
        "decision",
        "07_final_verification.json",
    )
