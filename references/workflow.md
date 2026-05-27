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
   - Blocks before analysis when evidence is incomplete or unsafe.

4. Analyst
   - Builds the decision frame, option evaluation, scenarios, recommendation, and rollup.
   - Blocks when audited evidence is insufficient for analysis.

5. Writer
   - Writes the reader-facing draft and internal writer trace.

6. Reviewer
   - Audits the draft and emits a structured review decision.
   - Uses `approved`, `targeted_revision`, or `needs_revision`.

7. Revision Writer
   - Runs only when the structured review decision requires it.
   - Writes the revised draft and revision trace.

8. Final Verifier
   - Emits the final publication gate.
   - Blocks publication when required revisions or evidence caveats are unresolved.

9. Publisher/system
   - Does not call Codex.
   - Copies the verified candidate to `08_final.md`, generates DOCX, and writes the manifest.

## State Rules

- Use `queued`, `running`, `publishing`, `completed`, `completed_markdown_only`, `blocked`, `needs_clarification`, `failed`, or `cancelled`.
- Keep `evidence_gate`, `analysis_gate`, `review_gate`, `revision_status`, and `final_gate` separate in `status.json`.
- Preserve old historical runs without migration.

## Context Rules

- Treat `00_task_contract.json` and `00_task_brief.md` as the shared context packet.
- Give each role only its prompt and required prior artifacts.
- OpenAI API direct calls are not allowed; semantic role execution stays inside `codex exec`.
