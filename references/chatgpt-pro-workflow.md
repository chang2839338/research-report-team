# ChatGPT Pro Workflow

Use this guide when running `research-report-team` through ChatGPT Pro and Codex without separate API calls.

The local web workflow avoids direct OpenAI API calls and keeps role artifacts aligned with the quality-first contract in `scripts/contracts.py`.

## Canonical Loop

00 Manager, 01 Researcher, 02 Evidence Auditor, 03 Analyst, 04 Writer, 05 Reviewer, 06 Revision Writer when needed, 07 Final Verifier, 08 Publisher/system.

Publisher is a system publication step. It does not call Codex and should not rewrite the verified candidate.

## Required Artifact Trail

- `artifacts/00_task_contract.json`
- `artifacts/00_task_brief.md`
- `artifacts/01_research.md`
- `artifacts/01_sources.md`
- `artifacts/01_claims.md`
- `artifacts/01_gaps.md`
- `artifacts/01_numeric_assumptions.md`
- `artifacts/01_source_provenance.md`
- `artifacts/02_evidence_gate.json`
- `artifacts/02_evidence_audit.md`
- `artifacts/03a_decision_frame.md`
- `artifacts/03b_option_evaluation.md`
- `artifacts/03c_scenarios_and_recommendation.md`
- `artifacts/03_analysis.md`
- `artifacts/03_analysis_status.json`
- `artifacts/04_draft.md`
- `artifacts/04_writer_trace.md`
- `artifacts/05_review_decision.json`
- `artifacts/05_review.md`
- `artifacts/05_claim_audit.md`
- `artifacts/06_revision.md`
- `artifacts/06_revision_trace.md`
- `artifacts/07_final_verification.json`
- `artifacts/07_final_verification.md`
- `artifacts/08_final.md`
- `artifacts/08_final.docx`
- `artifacts/08_final_manifest.json`
