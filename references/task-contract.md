# Task Contract Reference

Use this contract to keep role work consistent in the ChatGPT Pro skill workflow. This is not an API schema. It is a human-readable structure that can later be converted into JSON if independent agents are implemented.

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

## Artifact Types

- `research`: source-backed findings and source notes.
- `analysis`: criteria, option comparison, risks, and recommendation.
- `draft`: Writer's report draft.
- `review`: Reviewer score and revision request.
- `final`: final user-facing report.

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

