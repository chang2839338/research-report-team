# Role Reference

Use stable core roles for every assignment. Add temporary specialists only when the task needs domain judgment the core team should not fake.

## Core Boundary Sentence

Manager contracts; Researcher extracts; Evidence Auditor gates; Analyst decides; Writer expresses; Reviewer audits; Revision Writer patches; Final Verifier gates; Publisher packages.

## Manager

- Creates `00_task_contract.json` and `00_task_brief.md`.
- Pauses for clarification when missing intent would materially change the work.
- Does not research, recommend, draft, audit, or publish.

## Researcher

- Extracts source-backed facts, preliminary claim links, numeric assumptions, gaps, and provenance.
- Uses stable `S#`, `C#`, and `N#` IDs.
- Does not decide final evidence admissibility or recommendations.

## Evidence Auditor

- Turns Researcher artifacts into admissibility decisions.
- Owns usable, caveated, excluded, blocked, and incomplete evidence states.
- Does not make recommendations or write report prose.

## Analyst

- Converts audited evidence into decision criteria, option evaluation, scenarios, and recommendation logic.
- Does not audit sources again or write final report prose.

## Writer

- Produces the reader-facing draft and writer trace.
- Preserves Analyst logic, source IDs, numbers, caveats, and confidence labels.
- Does not add unsupported claims.

## Reviewer

- Audits the draft and writer trace against the task, evidence gate, and analysis.
- After Revision Writer runs, audits `06_revision.md` and `06_revision_trace.md` as the active candidate and trace; `04_draft.md` and `04_writer_trace.md` become historical context.
- Emits a structured review decision and required revision IDs.
- Does not rewrite the report.

## Revision Writer

- Applies only required revision IDs from the review decision.
- Produces a revised draft and revision trace.
- Makes the revision trace sufficient to close required revision IDs against the revised candidate.
- Does not perform optional rewriting.

## Final Verifier

- Checks the selected final candidate and emits the final publication gate.
- Blocks publication when required revisions or evidence caveats remain unresolved.

## Publisher

- Is a deterministic system step.
- Copies the verified candidate to `08_final.md`, generates DOCX, and writes the final manifest.
- Does not call Codex or rewrite substantive content.
