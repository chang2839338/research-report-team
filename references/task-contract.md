# Task Contract Reference

Use this contract to keep role work consistent in the Codex quality-first workflow.

## Task Brief

Every run starts with `artifacts/00_task_brief.md`:

```json
{
  "title": "Short task title",
  "user_request": "Original user request",
  "decision_goal": "Decision or report goal",
  "target_reader": "Who will read or use the result",
  "output_format": "Decision brief, executive report, research memo, or custom format",
  "scope": ["Included topic or boundary"],
  "exclusions": ["Out of scope item"],
  "acceptance_criteria": ["The final output answers the decision goal"],
  "assumptions": ["Assumption visible to the user"],
  "canonical_artifact_plan": ["00 through 08 workflow artifacts"]
}
```

## Canonical Artifacts

- `00_task_brief.md`: Manager task brief and shared context packet.
- `01_research.md`: Research memo.
- `01_sources.md`: Source ledger.
- `01_claims.md`: Claim evidence table.
- `01_gaps.md`: Research gaps and risks.
- `01_numeric_assumptions.md`: Numeric assumptions ledger.
- `02_evidence_audit.md`: Evidence Auditor output.
- `03_analysis.md`: Analyst criteria, scenarios, tradeoffs, and recommendation.
- `04_draft.md`: Writer draft.
- `05_review.md`: Reviewer score and claim audit.
- `06_revision.md`: Revision Writer output when required.
- `07_final_verification.md`: Final Verifier quality gate.
- `08_final.md`: Publisher final Markdown report.
- `08_final.docx`: Locally generated Word report.
- `08_final_manifest.json`: Publication metadata.

## Role Boundaries

- Researcher gathers evidence and flags uncertainty; it does not make the final recommendation.
- Evidence Auditor blocks unsupported or untraceable claims before analysis.
- Analyst recommends only from audited evidence and visible assumptions.
- Writer drafts from prior artifacts; it does not invent facts for polish.
- Reviewer scores and requests targeted revisions; it does not silently rewrite the report.
- Revision Writer applies only requested, evidence-supported changes.
- Final Verifier checks whether the final candidate is publishable.
- Publisher writes `08_final.md`; the server writes DOCX and manifest.

## Auto-Progress State

`status.json` should include:

```json
{
  "state": "running",
  "current_role": "analyst",
  "completed_roles": ["manager", "researcher", "evidence_auditor"],
  "revision_count": 0,
  "quality_gate": {"decision": "not_started"},
  "docx_status": "missing",
  "agent_runs": []
}
```

Set `completed` only after `08_final.md`, `08_final.docx`, and `08_final_manifest.json` exist.
