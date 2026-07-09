#!/usr/bin/env python3
"""Create a local research-report-team task workspace.

The CLI prepares the same quality-first contract used by the web server. It does
not call an LLM, Codex sub-agent, OpenAI API, or any network service.
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from store import RunStore


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


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a research report team task workspace.")
    parser.add_argument("brief", help="User request or decision brief.")
    parser.add_argument("--title", default=None, help="Report title. Defaults to the first part of the brief.")
    parser.add_argument("--out", default="runs", help="Output directory for task workspaces.")
    parser.add_argument(
        "--workflow",
        choices=["chatgpt-pro-skill", "codex-subagent-workflow", "codex-quality-first-local-web"],
        default="codex-quality-first-local-web",
        help="Workflow label to record in task.json. The CLI still only creates workspace files.",
    )
    parser.add_argument(
        "--auto-progress",
        action="store_true",
        help="Record that the Manager should run roles without approval gates unless blocked.",
    )
    args = parser.parse_args()

    title = args.title or args.brief[:80].strip()
    timestamp = datetime.now().astimezone().strftime("%Y%m%d_%H%M")
    out_dir = Path(args.out)
    task_dir = unique_task_dir(out_dir, timestamp)
    task_dir.mkdir(parents=True, exist_ok=False)

    store = RunStore(out_dir)
    store.scaffold_workspace(
        task_dir,
        title=title,
        brief=args.brief,
        workflow=args.workflow,
        auto_progress=args.auto_progress,
    )

    print(task_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

