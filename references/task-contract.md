# Task Contract Reference

Use this contract to keep role work consistent in the ChatGPT Pro skill workflow
and the Codex sub-agent workflow. This is not an API schema. It is a
human-readable structure that can later be converted into JSON if an API runner
is implemented.

## Task Brief

Every task should be reduced to this shape before role work begins:

```json
{
  "task_id": "T-001",
  "title": "Short task title",
  "user_request": "Original user request",
  "decision_goal": "Decision or report goal",
  "target_reader": "Who will read or use the result",
  "output_format": "Decision brief, executive report, research memo, or custom format",
  "scope": ["Included topic or boundary"],
  "exclusions": ["Out of scope item"],
  "constraints": ["Deadline, language, length, source requirement, or other limit"],
  "acceptance_criteria": [
    "The final output answers the decision goal",
    "Current factual claims include sources",
    "Recommendation follows from evidence"
  ],
  "assumptions": ["Assumption visible to the user"],
  "status": "intake"
}
```

## Role Task

Each role receives a smaller task:

```json
{
  "role": "Researcher",
  "goal": "Collect source-backed facts about the target market",
  "inputs": ["task brief", "user constraints"],
  "output_format": "Markdown findings with source notes",
  "acceptance_criteria": [
    "Separate facts from interpretation",
    "Include source links for current claims",
    "Flag uncertainty"
  ]
}
```

## Sub-Agent Contract

When a role is run as an independent Codex sub-agent, the Manager should provide
this minimum input package:

```json
{
  "role": "Researcher",
  "task_brief": "artifacts/00_task_brief.md",
  "role_prompt": "The prompt for this role",
  "previous_artifacts": {
    "research": "artifacts/01_research.md; only for roles after Researcher",
    "sources": "artifacts/01_sources.md; source ledger for Reviewer and final audit",
    "claims": "artifacts/01_claims.md; claim evidence table for roles after Researcher",
    "gaps": "artifacts/01_gaps.md; research gaps for roles after Researcher",
    "analysis": "artifacts/02_analysis.md; only for Writer and Reviewer",
    "draft": "artifacts/03_draft.md; only for Reviewer"
  },
  "acceptance_criteria": [
    "Role-specific criteria",
    "Final report criteria that affect this role"
  ],
  "output_artifact": "artifacts/01_research.md"
}
```

Every sub-agent output should include:

```markdown
## Artifact

[Role output in the requested format]

## Assumptions

- [Assumption used by the role]

## Source Notes

- [Source, citation, or note when applicable]

## Open Questions

- [Question or gap that may affect the next role]

## Confidence And Limitations

- [Confidence level and reason]
- [Limitation or missing information]
```

Role boundaries:

- Researcher gathers evidence and flags uncertainty; it does not make the final recommendation.
- Analyst compares options and recommends only when supported by the research.
- Writer drafts from approved research and analysis; it does not invent new facts for polish.
- Reviewer scores the draft and requests targeted revisions; it does not silently rewrite the whole report.
- Manager integrates artifacts, handles user feedback, and delivers `05_final.md` plus `05_final.docx`.

## Artifact Files

- `00_task_brief.md`: shared context packet and task contract for all roles.
- `01_research.md`: human-readable research memo.
- `01_sources.md`: source ledger with URLs, publishers, dates, credibility, relevance, and limitations.
- `01_claims.md`: claim evidence table with verification status.
- `01_gaps.md`: unsupported claims, evidence gaps, conflicts, and follow-up searches.
- `02_analysis.md`: criteria, option comparison, risks, and recommendation.
- `03_draft.md`: Writer's report draft.
- `04_review.md`: Reviewer score and revision request.
- `05_final.md`: final user-facing report.
- `05_final.docx`: Word version of the final report when a local workspace is available.

## Auto-Progress State

When a task workspace exists and the user has not requested manual approval
gates, role execution should auto-progress and persist artifacts after every
role.

`status.json` should use this shape:

```json
{
  "state": "running",
  "current_role": "Analyst",
  "completed_roles": ["Manager", "Researcher"],
  "pending_user_feedback": false,
  "auto_progress": true,
  "agent_runs": [
    {
      "role": "Researcher",
      "artifact": "artifacts/01_research.md",
      "extra_artifacts": [
        "artifacts/01_sources.md",
        "artifacts/01_claims.md",
        "artifacts/01_gaps.md"
      ],
      "status": "completed",
      "summary": "Collected source-backed findings"
    }
  ]
}
```

State rules:

- Set `auto_progress` to `true` when the Manager should continue without user approval.
- Set `pending_user_feedback` to `true` only when the user explicitly requested a review gate or a blocking clarification is required.
- Append an `agent_runs` entry after each role completes.
- Update the matching artifact file before moving to the next role.
- Set `state` to `needs_revision` when Reviewer returns `Needs revision`.
- Set `state` to `completed` only after `05_final.md` and `05_final.docx` have been produced.

## Example

User request:

```text
AI agent 팀을 웹앱으로 만들지, 우선 ChatGPT Pro 기반 skill로 운영할지 의사결정 보고서를 작성해줘.
```

Task brief:

```json
{
  "task_id": "T-001",
  "title": "AI agent team operating model decision",
  "user_request": "AI agent 팀을 웹앱으로 만들지, 우선 ChatGPT Pro 기반 skill로 운영할지 의사결정 보고서를 작성해줘.",
  "decision_goal": "Choose the near-term operating model for the research-report-team project",
  "target_reader": "Project owner",
  "output_format": "Decision brief",
  "scope": [
    "ChatGPT Pro skill workflow",
    "API/agent runner/web app option",
    "Cost and implementation complexity"
  ],
  "exclusions": [
    "Building the web app now",
    "Calling paid APIs now"
  ],
  "constraints": [
    "Prefer Korean explanation",
    "Avoid API costs unless justified"
  ],
  "acceptance_criteria": [
    "Compare both operating models",
    "Recommend a near-term path",
    "Explain when to revisit API/web app work"
  ],
  "assumptions": [
    "The user already has ChatGPT Pro",
    "The project is still in workflow validation stage"
  ],
  "status": "intake"
}
```

Role tasks:

```text
Researcher: gather facts about ChatGPT Pro vs API cost separation and practical workflow constraints.
Analyst: compare skill-first and API-first approaches by cost, complexity, automation value, and future extensibility.
Writer: draft a Korean decision brief.
Reviewer: check whether the recommendation is evidence-backed and action-ready.
```

