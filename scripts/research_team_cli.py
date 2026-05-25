#!/usr/bin/env python3
"""Create a portable research-report-team task workspace.

This CLI is intentionally small. It does not call an LLM yet; it creates a
structured task folder that a future API, worker, or web app can reuse.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


DECISION_BRIEF_TEMPLATE = """# {title}

## Executive Summary

TBD

## Decision To Make

{brief}

## Recommendation

TBD

## Options Compared

| Option | Strengths | Weaknesses | Best Fit | Key Risk |
| --- | --- | --- | --- | --- |

## Evidence

- TBD

## Risks And Caveats

- TBD

## Next Actions

1. TBD
"""


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
    now = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    task_dir = Path(args.out) / f"{now}-{slugify(title)}"
    task_dir.mkdir(parents=True, exist_ok=False)

    task = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "title": title,
        "brief": args.brief,
        "status": "intake",
        "roles": ["Manager", "Researcher", "Analyst", "Writer", "Reviewer"],
        "acceptance_criteria": [
            "Clarify decision goal and target reader",
            "Use source-backed evidence for factual claims",
            "Compare options against explicit criteria",
            "Deliver a decision-ready final report",
        ],
        "artifacts": {
            "task_brief": "task.json",
            "draft": "draft.md",
            "sources": "sources.md",
            "review": "review.md",
        },
    }

    (task_dir / "task.json").write_text(
        json.dumps(task, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (task_dir / "draft.md").write_text(
        DECISION_BRIEF_TEMPLATE.format(title=title, brief=args.brief),
        encoding="utf-8",
    )
    (task_dir / "sources.md").write_text("# Sources\n\n- TBD\n", encoding="utf-8")
    (task_dir / "review.md").write_text("# Review\n\nTBD\n", encoding="utf-8")

    print(task_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

