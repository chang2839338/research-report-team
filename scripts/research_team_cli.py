#!/usr/bin/env python3
"""Create a local research-report-team task workspace.

The CLI does not call an LLM, Codex sub-agent, or API. It prepares files that
make the research-report-team workflow easier to run and resume from a PC.
"""

from __future__ import annotations

import argparse
from html import escape
import json
from datetime import datetime
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


ROLES = [
    ("01", "manager"),
    ("02", "researcher"),
    ("03", "analyst"),
    ("04", "writer"),
    ("05", "reviewer"),
]

ARTIFACT_TEMPLATES = {
    "00_task_brief.md": "# Task Brief\n\nTBD\n",
    "01_research.md": "# Research\n\nTBD\n",
    "01_sources.md": "# Source Ledger\n\nTBD\n",
    "01_claims.md": "# Claim Evidence Table\n\nTBD\n",
    "01_gaps.md": "# Research Gaps And Risks\n\nTBD\n",
    "02_analysis.md": "# Analysis\n\nTBD\n",
    "03_draft.md": "# Draft\n\nTBD\n",
    "04_review.md": "# Review\n\nTBD\n",
    "05_final.md": "# Final Report\n\nTBD\n",
}


def unique_task_dir(out_dir: Path, timestamp: str) -> Path:
    task_dir = out_dir / timestamp
    if not task_dir.exists():
        return task_dir

    suffix = 1
    while True:
        candidate = out_dir / f"{timestamp}_{suffix:02d}"
        if not candidate.exists():
            return candidate
        suffix += 1


def skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def read_role_prompt(role: str) -> str:
    prompt_path = skill_root() / "prompts" / f"{role}.md"
    if not prompt_path.exists():
        return f"# {role.title()} Prompt\n\nTBD\n"
    return prompt_path.read_text(encoding="utf-8")


def task_context(title: str, brief: str, workflow: str) -> str:
    return (
        "# Task Context\n\n"
        f"- Title: {title}\n"
        f"- User request: {brief}\n"
        f"- Workflow: {workflow}.\n"
        "- This CLI creates workspace files only; it does not execute agents.\n"
        "- Treat artifacts/00_task_brief.md as the shared context packet.\n"
        "- Give each role only the task brief, its role prompt, acceptance criteria, and required prior artifacts.\n"
        "- Use the task contract and quality rubric from this repository.\n\n"
    )


def write_role_prompts(
    task_dir: Path, title: str, brief: str, workflow: str
) -> dict[str, str]:
    prompts_dir = task_dir / "prompts"
    prompts_dir.mkdir()
    prompt_paths = {}
    context = task_context(title, brief, workflow)

    for index, role in ROLES:
        content = context + read_role_prompt(role)
        relative_path = Path("prompts") / f"{index}_{role}.md"
        (task_dir / relative_path).write_text(content, encoding="utf-8")
        prompt_paths[role] = relative_path.as_posix()

    return prompt_paths


def write_artifacts(task_dir: Path, title: str) -> dict[str, str]:
    artifacts_dir = task_dir / "artifacts"
    artifacts_dir.mkdir()
    artifact_paths = {}

    for filename, content in ARTIFACT_TEMPLATES.items():
        relative_path = Path("artifacts") / filename
        (task_dir / relative_path).write_text(content, encoding="utf-8")
        artifact_paths[artifact_key(filename)] = relative_path.as_posix()

    docx_path = Path("artifacts") / "05_final.docx"
    write_minimal_docx(task_dir / docx_path, title=title, body="TBD")
    artifact_paths["final_docx"] = docx_path.as_posix()

    return artifact_paths


def artifact_key(filename: str) -> str:
    stem = Path(filename).stem
    if "_" not in stem:
        return stem
    return stem.split("_", 1)[1]


def write_minimal_docx(path: Path, title: str, body: str) -> None:
    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>
"""
    root_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>
"""
    document = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:r><w:t>{escape(title)}</w:t></w:r></w:p>
    <w:p><w:r><w:t>{escape(body)}</w:t></w:r></w:p>
    <w:sectPr><w:pgSz w:w="12240" w:h="15840"/><w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"/></w:sectPr>
  </w:body>
</w:document>
"""
    with ZipFile(path, "w", ZIP_DEFLATED) as docx:
        docx.writestr("[Content_Types].xml", content_types)
        docx.writestr("_rels/.rels", root_rels)
        docx.writestr("word/document.xml", document)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a research report team task workspace."
    )
    parser.add_argument("brief", help="User request or decision brief.")
    parser.add_argument(
        "--title",
        default=None,
        help="Report title. Defaults to the first part of the brief.",
    )
    parser.add_argument(
        "--out",
        default="runs",
        help="Output directory for task workspaces.",
    )
    parser.add_argument(
        "--workflow",
        choices=["chatgpt-pro-skill", "codex-subagent-workflow"],
        default="chatgpt-pro-skill",
        help=(
            "Workflow label to record in task.json. The CLI still only creates "
            "workspace files."
        ),
    )
    parser.add_argument(
        "--auto-progress",
        action="store_true",
        help=(
            "Record that the Manager should run roles without user approval "
            "gates and save each artifact before continuing."
        ),
    )
    args = parser.parse_args()

    title = args.title or args.brief[:80].strip()
    now = datetime.now().astimezone()
    created_at = now.isoformat()
    timestamp = now.strftime("%Y%m%d_%H%M")
    task_dir = unique_task_dir(Path(args.out), timestamp)
    task_dir.mkdir(parents=True, exist_ok=False)

    prompt_paths = write_role_prompts(task_dir, title, args.brief, args.workflow)
    artifact_paths = write_artifacts(task_dir, title)

    task = {
        "created_at": created_at,
        "title": title,
        "brief": args.brief,
        "workflow": args.workflow,
        "api_calls": False,
        "auto_progress": args.auto_progress,
        "agent_execution": (
            "codex-subagents"
            if args.workflow == "codex-subagent-workflow"
            else "single-manager-chat"
        ),
        "roles": ["Manager", "Researcher", "Analyst", "Writer", "Reviewer"],
        "acceptance_criteria": [
            "Clarify decision goal and target reader",
            "Use source-backed evidence for factual claims",
            "Compare options against explicit criteria",
            "Deliver a decision-ready final report",
        ],
        "prompts": prompt_paths,
        "artifacts": artifact_paths,
        "sources": "sources.md",
        "status": "status.json",
    }

    status = {
        "created_at": created_at,
        "updated_at": created_at,
        "state": "intake",
        "current_role": "Manager",
        "completed_roles": [],
        "pending_user_feedback": False,
        "auto_progress": args.auto_progress,
        "agent_runs": [],
        "next_step": "Open prompts/01_manager.md and start the task in ChatGPT Pro.",
        "notes": [],
    }

    if args.workflow == "codex-subagent-workflow":
        status["next_step"] = (
            "Start in Codex with prompts/01_manager.md; the Manager should spawn "
            "Researcher, Analyst, Writer, and Reviewer as sub-agents when tools "
            "are available."
        )

    if args.auto_progress:
        status["next_step"] += (
            " Auto-progress is enabled: save each role artifact to artifacts/*.md "
            "and continue without user approval gates unless blocked."
        )

    (task_dir / "task.json").write_text(
        json.dumps(task, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (task_dir / "status.json").write_text(
        json.dumps(status, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (task_dir / "sources.md").write_text("# Sources\n\n- TBD\n", encoding="utf-8")

    print(task_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

