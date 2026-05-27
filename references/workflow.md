# Workflow Reference

## Quality-First Team Loop

1. Manager
   - Writes `00_task_contract.json` and `00_task_brief.md`.
   - Stops with `needs_clarification` when user input is required.

2. Researcher
   - Extracts evidence, sources, preliminary claims, gaps, numbers, and provenance.
   - Writes the `01_*` research artifact set.

3. Evidence Auditor
   - Produces the authoritative admissibility gate.
   - Triggers targeted Researcher remediation when evidence is incomplete or unsafe.
   - After two failed remediation attempts, records unresolved evidence issues and continues with caveats.

4. Analyst
   - Builds the decision frame, option evaluation, scenarios, recommendation, and rollup.
   - Triggers Researcher/Evidence remediation when audited evidence is insufficient for analysis.
   - After two failed remediation attempts, records unresolved analysis issues and continues with caveats.

5. Writer
   - Writes the reader-facing draft and internal writer trace.

6. Reviewer
   - Audits the draft and emits a structured review decision.
   - Uses `approved`, `targeted_revision`, or `needs_revision`.
   - Required revisions trigger Revision Writer and Reviewer retry up to two times.

7. Revision Writer
   - Runs only when the structured review decision requires it.
   - Writes the revised draft and revision trace.

8. Final Verifier
   - Emits the final publication gate.
   - Triggers Revision Writer and final verification retry when required revisions or evidence caveats are unresolved.
   - After two failed remediation attempts, records unresolved final issues and allows conditional publication.

9. Publisher/system
   - Does not call Codex.
   - Copies the verified candidate to `08_final.md`, generates DOCX, and writes the manifest.

## State Rules

- Use `queued`, `running`, `remediating`, `continuing_with_issues`, `publishing`, `completed`, `completed_with_unresolved_issues`, `completed_markdown_only`, `blocked`, `needs_clarification`, `failed`, or `cancelled`.
- Keep `evidence_gate`, `analysis_gate`, `review_gate`, `revision_status`, and `final_gate` separate in `status.json`.
- Keep exhausted gate issues in `unresolved_gate_issues` and carry them into downstream prompts.
- Preserve old historical runs without migration.

## Context Rules

- Treat `00_task_contract.json` and `00_task_brief.md` as the shared context packet.
- Give each role only its prompt and required prior artifacts.
- OpenAI API direct calls are not allowed; semantic role execution stays inside `codex exec`.
