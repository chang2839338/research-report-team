# ChatGPT Pro Workflow

Use this guide when running `research-report-team` through ChatGPT Pro and Codex without separate API calls.

## Purpose

This workflow lets a user run a research and report-writing team from a normal ChatGPT/Codex chat. It avoids direct OpenAI API calls and keeps the role contract aligned with the local quality-first web workflow.

## Recommended Chat Start Prompt

```text
Use the research-report-team skill.

Act as the Manager of a decision research and report-writing team.
Use the canonical quality-first workflow:
00 Manager, 01 Researcher, 02 Evidence Auditor, 03 Analyst, 04 Writer, 05 Reviewer, 06 Revision Writer when needed, 07 Final Verifier, 08 Publisher.

For current factual claims, keep source traceability.
For numbers, keep a numeric assumptions ledger.
Before final delivery, review and verify the draft.

My request:
[paste the decision or report request here]
```

## Local Artifact Set

- `artifacts/00_task_brief.md`
- `artifacts/01_research.md`
- `artifacts/01_sources.md`
- `artifacts/01_claims.md`
- `artifacts/01_gaps.md`
- `artifacts/01_numeric_assumptions.md`
- `artifacts/02_evidence_audit.md`
- `artifacts/03_analysis.md`
- `artifacts/04_draft.md`
- `artifacts/05_review.md`
- `artifacts/06_revision.md`
- `artifacts/07_final_verification.md`
- `artifacts/08_final.md`
- `artifacts/08_final.docx`
- `artifacts/08_final_manifest.json`

## Saving Outputs Locally

Use the CLI to create a local workspace:

```powershell
python .\scripts\research_team_cli.py "your report request" --title "short title"
```

Start from `prompts/00_manager.md` when pasting task context into ChatGPT Pro.
