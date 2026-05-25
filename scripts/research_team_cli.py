#!/usr/bin/env python3
"""Create a local research-report-team task workspace.

The CLI does not call an LLM or API. It prepares files that make the
ChatGPT Pro skill workflow easier to run and resume from a PC.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


ROLES = ["manager", "researcher", "analyst", "writer", "reviewer"]

ARTIFACT_TEMPLATES = {
    "research.md": "# Research\n\nTBD\n",
    "analysis.md": "# Analysis\n\nTBD\n",
    "draft.md": "# Draft\n\nTBD\n",
    "review.md": "# Review\n\nTBD\n",
    "final.md": "# Final Report\n\nTBD\n",
}


def slugify(value: str) -> str:
    allowed = []
    for char in value.lower():
        if char.isalnum():
            allowed.append(char)
        elif char in {" ", "-", "_"}:
            allowed.append("-")
    slug = "".join(allowed).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug[:60] or "research-task"


def skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def read_role_prompt(role: str) -> str:
    prompt_path = skill_root() / "prompts" / f"{role}.md"
    if not prompt_path.exists():
        return f"# {role.title()} Prompt\n\nTBD\n"
    return prompt_path.read_text(encoding="utf-8")


def task_context(title: str, brief: str) -> str:
    return (
        "# Task Context\n\n"
        f"- Title: {title}\n"
        f"- User request: {brief}\n"
        "- Workflow: ChatGPT Pro + Codex Skill, no API calls.\n"
        "- Use the task contract and quality rubric from this repository.\n\n"
    )


def write_role_prompts(task_dir: Path, title: str, brief: str) -> dict[str, str]:
    prompts_dir = task_dir / "prompts"
    prompts_dir.mkdir()
    prompt_paths = {}
    context = task_context(title, brief)

    for role in ROLES:
        content = context + read_role_prompt(role)
        relative_path = Path("prompts") / f"{role}.md"
        (task_dir / relative_path).write_text(content, encoding="utf-8")
        prompt_paths[role] = relative_path.as_posix()

    return prompt_paths


def write_artifacts(task_dir: Path) -> dict[str, str]:
    artifacts_dir = task_dir / "artifacts"
    artifacts_dir.mkdir()
    artifact_paths = {}

    for filename, content in ARTIFACT_TEMPLATES.items():
        relative_path = Path("artifacts") / filename
        (task_dir / relative_path).write_text(content, encoding="utf-8")
        artifact_paths[Path(filename).stem] = relative_path.as_posix()

    return artifact_paths


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
        default="research-team-runs",
        help="Output directory for task workspaces.",
    )
    args = parser.parse_args()

    title = args.title or args.brief[:80].strip()
    created_at = datetime.now(timezone.utc).isoformat()
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    task_dir = Path(args.out) / f"{timestamp}-{slugify(title)}"
    task_dir.mkdir(parents=True, exist_ok=False)

    prompt_paths = write_role_prompts(task_dir, title, args.brief)
    artifact_paths = write_artifacts(task_dir)

    task = {
        "created_at": created_at,
        "title": title,
        "brief": args.brief,
        "workflow": "chatgpt-pro-skill",
        "api_calls": False,
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
        "completed_roles": [],
        "next_step": "Open prompts/manager.md and start the task in ChatGPT Pro.",
        "notes": [],
    }

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

