# Workflow Reference

## Team Loop

1. Intake
   - Restate the request in one or two sentences.
   - Identify missing details that materially affect the result.
   - Ask one focused question when needed.

2. Task Brief
   - Decision goal
   - Target reader
   - Output format
   - Scope and exclusions
   - Constraints
   - Acceptance criteria
   - Assumptions
   - Save as `artifacts/00_task_brief.md` when a workspace exists.

3. Work Plan
   - Break the work into 3-6 tasks.
   - Assign each task to a role.
   - Define expected output for each task.

4. Researcher Agent
   - Browse or inspect provided materials when current facts or citations matter.
   - Keep source notes compact and auditable.
   - Prefer primary or authoritative sources for high-stakes claims.
   - Save or present the output as `01_research.md`, `01_sources.md`, `01_claims.md`, and `01_gaps.md`.

5. Auto-Save Checkpoint
   - Write the Researcher artifacts to `artifacts/01_research.md`, `artifacts/01_sources.md`, `artifacts/01_claims.md`, and `artifacts/01_gaps.md` when a workspace exists.
   - Show a short progress summary to the user.
   - Continue to Analyst without waiting for approval unless a blocking clarification is required.

6. Analyst Agent
   - Define criteria before comparing options.
   - Make tradeoffs explicit.
   - Separate recommendation from supporting evidence.
   - Use `00_task_brief.md`, `01_research.md`, `01_claims.md`, and `01_gaps.md` as inputs.
   - Save or present the output as `02_analysis.md`.

7. Auto-Save Checkpoint
   - Write the Analyst artifact to `artifacts/02_analysis.md` when a workspace exists.
   - Show a short progress summary to the user.
   - Continue to Writer without waiting for approval unless a blocking clarification is required.

8. Writer Agent
   - Use the user's requested format first.
   - If absent, use a decision brief.
   - Preserve citations, caveats, and assumptions.
   - Use `00_task_brief.md`, `01_research.md`, `01_claims.md`, and `02_analysis.md` as inputs.
   - Save or present the output as `03_draft.md`.

9. Auto-Save Checkpoint
   - Write the Writer draft to `artifacts/03_draft.md` when a workspace exists.
   - Show a short progress summary to the user.
   - Continue to Reviewer without waiting for approval unless a blocking clarification is required.

10. Reviewer Agent
   - Score against the quality rubric.
   - Request revision for material failures.
   - Limit revision requests to the smallest useful set.
   - Use `00_task_brief.md`, `01_sources.md`, `01_claims.md`, `01_gaps.md`, `02_analysis.md`, `03_draft.md`, and the rubric as inputs.
   - Save or present the output as `04_review.md`.

11. Revision Loop
   - If Reviewer marks the draft `Needs revision`, request the smallest targeted revision.
   - Use a new Writer or Analyst agent when the revision requires independent role work.
   - Reuse the existing artifacts only as inputs; do not silently overwrite the review rationale.
   - Use at most two internal revision loops unless the user explicitly asks for exhaustive refinement.

12. Final Delivery
   - Lead with answer and recommendation.
   - Include evidence, rationale, risks, caveats, and next actions.
   - Mention unverified assumptions.
   - Save or present the final report as `05_final.md`.
   - Generate `05_final.docx` from the approved final Markdown when a local workspace is available.

## Codex Sub-Agent Workflow

When Codex sub-agent tools are available, the Manager should run this sequence:

```text
Intake -> 00_task_brief.md -> Researcher Agent -> Auto-Save Checkpoint
-> Analyst Agent -> Auto-Save Checkpoint
-> Writer Agent -> Auto-Save Checkpoint
-> Reviewer Agent -> Revision Loop -> Final
```

Each role agent receives only `00_task_brief.md`, its role prompt, acceptance
criteria, and the previous numbered artifacts required for that role. The
Manager should not pass unlimited conversation context unless the task explicitly
depends on it.

The default Codex sub-agent workflow is auto-progressing: the Manager should not
wait for user approval between roles unless the user explicitly requested review
gates, a required clarification blocks the next role, or continuing would create
a high-risk unsupported report.

When a local task workspace is available, every completed role artifact must be
written to the matching numbered file under `artifacts/` before the next role
begins. The Manager should also keep `status.json` aligned with the current role,
completed roles, feedback state, and known agent run metadata.

If sub-agent tools are unavailable, the Manager may run the same sequence in a
single chat, but must label the role work as simulated rather than independently
executed.

## Revision Rules

Request revision when:
- The output does not answer the decision goal.
- The recommendation is unsupported.
- Current factual claims lack citations.
- Important alternatives, risks, or constraints are missing.
- The format does not match the user's requested deliverable.
- Reviewer score is below 13/16.

Use at most two internal revision loops unless the user explicitly asks for exhaustive refinement.

## Web-App Ready Design Notes

Keep agent-team logic independent from the interface:
- Core: task brief, roles, workflow, review loop, report template.
- Interfaces: Codex skill, CLI, API, web app, mobile web.
- Storage: task state, messages, sources, artifacts, review notes.
