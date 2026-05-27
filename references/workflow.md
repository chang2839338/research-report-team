# Workflow Reference

## Quality-First Team Loop

1. Manager
   - Clarify the user request only when needed.
   - Save the shared task brief as `artifacts/00_task_brief.md`.
   - Include the canonical artifact plan in the task brief.

2. Researcher
   - Gather current evidence, sources, claim status, gaps, and numeric assumptions.
   - Save `01_research.md`, `01_sources.md`, `01_claims.md`, `01_gaps.md`, and `01_numeric_assumptions.md`.

3. Evidence Auditor
   - Audit source, claim, and numeric traceability before analysis.
   - Save `02_evidence_audit.md`.

4. Analyst
   - Use audited evidence to define criteria, anchor values, adjustment logic, scenarios, risks, and recommendation.
   - Save `03_analysis.md`.

5. Writer
   - Draft the user-facing report without adding unsupported claims.
   - Save `04_draft.md`.

6. Reviewer
   - Score the draft and audit material factual and numeric claims.
   - Save `05_review.md`.
   - Use `Approved`, `Approved with targeted revisions`, or `Needs revision`.

7. Revision Writer
   - Run only when Reviewer requests targeted revision or marks the draft as needing revision.
   - Save `06_revision.md`.

8. Final Verifier
   - Verify the final candidate before publication.
   - Save `07_final_verification.md`.

9. Publisher
   - Produce the final Markdown report as `08_final.md`.
   - The server then creates `08_final.docx` and `08_final_manifest.json`.
   - Mark the run `completed` only when all final publication artifacts exist.

## State Rules

- Use `queued`, `running`, `needs_revision`, `publishing`, `completed`, `completed_markdown_only`, `failed`, or `cancelled`.
- Set `needs_revision` after Reviewer returns `Needs revision` or `Approved with targeted revisions`.
- Preserve old historical runs without migration; new runs use the `08_*` final artifact names.

## Context Rules

- Treat `00_task_brief.md` as the shared context packet.
- Give each role only its prompt and required prior artifacts.
- Do not pass unlimited chat history unless the task explicitly depends on it.
- OpenAI API direct calls are not allowed; role execution stays inside `codex exec`.
