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

3. Work Plan
   - Break the work into 3-6 tasks.
   - Assign each task to a role.
   - Define expected output for each task.

4. Research
   - Browse or inspect provided materials when current facts or citations matter.
   - Keep source notes compact.
   - Prefer primary or authoritative sources for high-stakes claims.

5. Analysis
   - Define criteria before comparing options.
   - Make tradeoffs explicit.
   - Separate recommendation from supporting evidence.

6. Draft
   - Use the user's requested format first.
   - If absent, use a decision brief.
   - Preserve citations, caveats, and assumptions.

7. Review
   - Score against the quality rubric.
   - Request revision for material failures.
   - Limit revision requests to the smallest useful set.

8. Final Delivery
   - Lead with answer and recommendation.
   - Include evidence, rationale, risks, caveats, and next actions.
   - Mention unverified assumptions.

## Revision Rules

Request revision when:
- The output does not answer the decision goal.
- The recommendation is unsupported.
- Current factual claims lack citations.
- Important alternatives, risks, or constraints are missing.
- The format does not match the user's requested deliverable.

Use at most two internal revision loops unless the user explicitly asks for exhaustive refinement.

## Web-App Ready Design Notes

Keep agent-team logic independent from the interface:
- Core: task brief, roles, workflow, review loop, report template.
- Interfaces: Codex skill, CLI, API, web app, mobile web.
- Storage: task state, messages, sources, artifacts, review notes.

