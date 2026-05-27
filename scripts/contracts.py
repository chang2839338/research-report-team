"""Workflow and artifact contracts for the research report team."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


MARKER_PREFIX = "<!-- artifact:"
MARKER_SUFFIX = "-->"


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

    @property
    def primary_artifact(self) -> str:
        return self.artifacts[0].path

    @property
    def artifact_paths(self) -> list[str]:
        return [artifact.path for artifact in self.artifacts]


DEFAULT_ARTIFACT_TEMPLATES: dict[str, str] = {
    "00_task_brief.md": "# Task Brief\n\nTBD\n",
    "01_research.md": "# Research Memo\n\nTBD\n",
    "01_sources.md": "# Source Ledger\n\nTBD\n",
    "01_claims.md": "# Claim Evidence Table\n\nTBD\n",
    "01_gaps.md": "# Research Gaps And Risks\n\nTBD\n",
    "01_numeric_assumptions.md": "# Numeric Assumptions Ledger\n\nTBD\n",
    "02_evidence_audit.md": "# Evidence Audit\n\nTBD\n",
    "03_analysis.md": "# Analysis\n\nTBD\n",
    "04_draft.md": "# Draft\n\nTBD\n",
    "05_review.md": "# Review\n\nTBD\n",
    "06_revision.md": "# Revision\n\nTBD\n",
    "07_final_verification.md": "# Final Verification\n\nTBD\n",
    "08_final.md": "# Final Report\n\nTBD\n",
}


WORKFLOW: tuple[RoleSpec, ...] = (
    RoleSpec(
        key="manager",
        role="Manager",
        display_role="Manager",
        label="Task Brief",
        prompt="manager.md",
        prompt_file="00_manager.md",
        artifacts=(ArtifactSpec("00_task_brief.md", "Task Brief"),),
        goal="Create the task brief that guides every later role.",
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
        ),
        inputs=("00_task_brief.md",),
        goal="Gather source-backed findings, uncertainty notes, and numeric assumptions.",
    ),
    RoleSpec(
        key="evidence_auditor",
        role="Evidence Auditor",
        display_role="Evidence Audit",
        label="Evidence Audit",
        prompt="evidence_auditor.md",
        prompt_file="02_evidence_auditor.md",
        artifacts=(ArtifactSpec("02_evidence_audit.md", "Evidence Audit"),),
        inputs=(
            "00_task_brief.md",
            "01_research.md",
            "01_sources.md",
            "01_claims.md",
            "01_gaps.md",
            "01_numeric_assumptions.md",
        ),
        goal="Audit source traceability and block unsupported claims before analysis.",
    ),
    RoleSpec(
        key="analyst",
        role="Analyst",
        display_role="Analyst",
        label="Analysis",
        prompt="analyst.md",
        prompt_file="03_analyst.md",
        artifacts=(ArtifactSpec("03_analysis.md", "Analysis"),),
        inputs=(
            "00_task_brief.md",
            "01_research.md",
            "01_claims.md",
            "01_gaps.md",
            "01_numeric_assumptions.md",
            "02_evidence_audit.md",
        ),
        goal="Turn audited evidence into criteria, scenarios, tradeoffs, and recommendation.",
    ),
    RoleSpec(
        key="writer",
        role="Writer",
        display_role="Writer",
        label="Draft",
        prompt="writer.md",
        prompt_file="04_writer.md",
        artifacts=(ArtifactSpec("04_draft.md", "Draft"),),
        inputs=(
            "00_task_brief.md",
            "01_research.md",
            "01_claims.md",
            "01_numeric_assumptions.md",
            "02_evidence_audit.md",
            "03_analysis.md",
        ),
        goal="Draft a decision-ready report with clear certainty labels.",
    ),
    RoleSpec(
        key="reviewer",
        role="Reviewer",
        display_role="Reviewer",
        label="Review",
        prompt="reviewer.md",
        prompt_file="05_reviewer.md",
        artifacts=(ArtifactSpec("05_review.md", "Review"),),
        inputs=(
            "00_task_brief.md",
            "01_sources.md",
            "01_claims.md",
            "01_gaps.md",
            "01_numeric_assumptions.md",
            "02_evidence_audit.md",
            "03_analysis.md",
            "04_draft.md",
        ),
        extra_inputs=("references/report-quality-rubric.md",),
        goal="Audit the full draft and decide whether targeted revision is required.",
    ),
    RoleSpec(
        key="revision_writer",
        role="Revision Writer",
        display_role="Revision",
        label="Revision",
        prompt="revision_writer.md",
        prompt_file="06_revision_writer.md",
        artifacts=(ArtifactSpec("06_revision.md", "Revised Draft"),),
        inputs=(
            "00_task_brief.md",
            "01_sources.md",
            "01_claims.md",
            "01_gaps.md",
            "01_numeric_assumptions.md",
            "02_evidence_audit.md",
            "03_analysis.md",
            "04_draft.md",
            "05_review.md",
        ),
        goal="Apply the smallest useful revision requested by the Reviewer.",
        conditional="review_requires_revision",
    ),
    RoleSpec(
        key="final_verifier",
        role="Final Verifier",
        display_role="Final Verify",
        label="Final Verification",
        prompt="final_verifier.md",
        prompt_file="07_final_verifier.md",
        artifacts=(ArtifactSpec("07_final_verification.md", "Final Verification"),),
        inputs=(
            "00_task_brief.md",
            "01_sources.md",
            "01_claims.md",
            "01_gaps.md",
            "01_numeric_assumptions.md",
            "02_evidence_audit.md",
            "03_analysis.md",
            "04_draft.md",
            "05_review.md",
            "06_revision.md",
        ),
        extra_inputs=("references/quality-checklist.md",),
        goal="Verify that the final candidate is ready to publish.",
    ),
    RoleSpec(
        key="publisher",
        role="Publisher",
        display_role="Publisher",
        label="Final Report",
        prompt="manager.md",
        prompt_file="08_publisher.md",
        artifacts=(ArtifactSpec("08_final.md", "Final Report"),),
        inputs=(
            "00_task_brief.md",
            "01_sources.md",
            "01_claims.md",
            "01_gaps.md",
            "01_numeric_assumptions.md",
            "02_evidence_audit.md",
            "03_analysis.md",
            "04_draft.md",
            "05_review.md",
            "06_revision.md",
            "07_final_verification.md",
        ),
        goal="Publish the final Markdown report. The server creates 08_final.docx and 08_final_manifest.json.",
    ),
)


def all_artifact_paths() -> list[str]:
    paths: list[str] = []
    for role in WORKFLOW:
        for artifact in role.artifacts:
            if artifact.path not in paths:
                paths.append(artifact.path)
    return [*paths, "08_final.docx", "08_final_manifest.json"]


def public_roles() -> list[dict[str, Any]]:
    roles: list[dict[str, Any]] = []
    for role in WORKFLOW:
        roles.append(
            {
                "key": role.key,
                "role": role.role,
                "display_role": role.display_role,
                "label": role.label,
                "prompt": f"prompts/{role.prompt_file}",
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
        ("artifacts/08_final_manifest.json", "Final Manifest"),
        ("error.log", "Error Log"),
        ("events.ndjson", "Event Log"),
    ]:
        target = run_dir / path
        manifest.append(
            {
                "role_key": "system",
                "label": label,
                "path": path,
                "required": path.startswith("artifacts/08_final")
                or path.endswith("08_final_manifest.json"),
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
        parsed[name] = content + "\n"
    return parsed


def review_requires_revision(review_text: str) -> bool:
    lowered = review_text.lower()
    return (
        "needs revision" in lowered
        or "approved with targeted revisions" in lowered
        or "targeted revision" in lowered
        or "수정 필요" in review_text
    )
