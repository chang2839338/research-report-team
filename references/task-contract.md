# Task Contract Reference

Use this contract to keep role work consistent in the Codex quality-first workflow.

## Manager Contract

Every run starts with `artifacts/00_task_contract.json` and `artifacts/00_task_brief.md`.

Required JSON fields:

```json
{
  "contract_version": "quality-first-v2",
  "workflow_status": "ready",
  "clarifying_questions": [],
  "decision_goal": "",
  "target_reader": "",
  "output": {},
  "scope": {},
  "evidence_policy": {},
  "analysis_plan": {},
  "acceptance_criteria": [],
  "assumptions": [],
  "role_tasks": {}
}
```

`workflow_status` is either `ready` or `needs_user_input`.

## Role Boundaries

- Manager contracts the work.
- Researcher extracts evidence.
- Evidence Auditor gates evidence use.
- Analyst models the decision.
- Writer expresses the report for the reader.
- Reviewer audits the draft and trace.
- Revision Writer applies required revision IDs only.
- Final Verifier gates publication.
- Publisher is deterministic system packaging.

## Canonical Artifacts

The canonical artifact list is defined in `scripts/contracts.py`. New roles or artifacts must be added there first, then reflected in prompts, docs, UI, and tests.

## Completion Rule

Set `completed` only after `08_final.md`, `08_final.docx`, and `08_final_manifest.json` exist.
