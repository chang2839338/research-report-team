# research-report-team Final Work Plan

## Summary

`research-report-team` is an AI team system for decision research and report writing. The current version is a Codex Skill that lets one Codex instance act as the Manager and perform multiple team roles in sequence. The system should evolve step by step: stable role prompts and contracts, a stronger CLI runner, independent LLM agent execution, API service, and finally a web app usable from PC and mobile.

This plan is the implementation roadmap for developing the repository without jumping too early into a complex multi-worker architecture.

## Current State

The repository currently contains the first usable skill version:

- `SKILL.md`: main Codex Skill instructions.
- `agents/openai.yaml`: UI-facing skill metadata.
- `references/roles.md`: detailed Manager, Researcher, Analyst, Writer, Reviewer role definitions.
- `references/workflow.md`: team workflow and revision loop.
- `references/report-quality-rubric.md`: final report review rubric.
- `references/output-templates.md`: reusable decision brief, executive report, and research memo templates.
- `scripts/research_team_cli.py`: small CLI that creates a structured task workspace.

The current operating model is intentionally simple: one Codex instance follows the skill and simulates the team workflow. This is the right MVP because it validates the workflow, prompts, report shape, and quality gate before adding independent agent infrastructure.

## Development Roadmap

### Phase 1: Codex Skill MVP

Status: complete.

Goal:

- Provide a reusable Codex Skill for decision research and report writing.
- Define stable core roles and a controlled review loop.
- Keep the workflow portable through GitHub.

Deliverables:

- Skill instructions.
- Role reference.
- Workflow reference.
- Report quality rubric.
- Output templates.
- Minimal CLI workspace creator.

Validation:

- Run the skill validator.
- Run the CLI with a sample brief.
- Confirm the created workspace includes `task.json`, `draft.md`, `sources.md`, and `review.md`.

### Phase 2: Role Prompts And JSON Contracts

Goal:

- Make the role behavior explicit enough to later move each role into an independent LLM call.
- Keep the single-Codex workflow working while preparing for automation.

Planned additions:

- `prompts/manager.md`
- `prompts/researcher.md`
- `prompts/analyst.md`
- `prompts/writer.md`
- `prompts/reviewer.md`
- `schemas/task.schema.json`
- `schemas/artifact.schema.json`
- `schemas/review.schema.json`

Expected behavior:

- The Manager prompt clarifies the user goal, creates the task brief, assigns work, reviews progress, and delivers the final report.
- The Researcher prompt gathers source-backed facts and separates evidence from interpretation.
- The Analyst prompt compares options against explicit criteria and produces recommendations.
- The Writer prompt turns approved findings into the requested report format.
- The Reviewer prompt scores the draft against the rubric and produces targeted revision requests.

Validation:

- Check that each prompt has clear inputs, outputs, and failure rules.
- Validate JSON schemas.
- Create one sample task and confirm it can be represented by the schemas.

### Phase 3: CLI Runner Upgrade

Goal:

- Turn the CLI from a workspace creator into a repeatable local execution interface.
- Preserve all state in files so the workflow remains easy to inspect and later wrap with an API.

Planned CLI capabilities:

- Create a task workspace from a brief.
- Generate role-specific prompt files for the task.
- Store role artifacts in a predictable folder.
- Store reviewer scores and revision requests.
- Record task status transitions.

Recommended workspace shape:

```text
research-team-runs/
  <timestamp-task-slug>/
    task.json
    prompts/
      manager.md
      researcher.md
      analyst.md
      writer.md
      reviewer.md
    artifacts/
      research.md
      analysis.md
      draft.md
      review.md
      final.md
    sources.md
    status.json
```

Validation:

- Run the CLI with a sample brief.
- Confirm the workspace shape is created.
- Confirm generated prompts include task-specific context.
- Confirm status files are valid JSON.

### Phase 4: Independent Agent Runner

Goal:

- Move from one Codex instance simulating roles to separate LLM calls per role.
- Keep the Manager responsible for orchestration, acceptance criteria, and revision decisions.

Planned behavior:

- Manager creates a structured task brief.
- Researcher, Analyst, Writer, and Reviewer each run as separate LLM calls.
- Each role receives only the inputs it needs and returns a structured artifact.
- Reviewer can trigger targeted revisions.
- The runner stops after a bounded number of revision loops.

Default execution model:

- Sequential execution first.
- Parallel research subtasks only after sequential behavior is reliable.
- File-based state first.
- Database-backed state only when moving to API/web app.

Validation:

- Run a sample report end to end.
- Confirm each role produces its own artifact.
- Confirm reviewer failures create specific revision requests.
- Confirm final report includes recommendation, evidence, risks, assumptions, and next actions.

### Phase 5: API And Web App

Goal:

- Make the research team usable from a browser on PC and mobile.
- Allow users to create tasks, answer clarification questions, monitor progress, and receive final reports.

Recommended architecture:

```text
Frontend
  PC/mobile responsive web UI

Backend API
  task creation
  task status
  messages and clarification answers
  artifact retrieval

Worker
  agent team execution
  long-running background jobs

Storage
  database for tasks, messages, sources, artifacts, reviews
  file/object storage for reports
```

Recommended defaults:

- Backend: FastAPI.
- Frontend: React or Next.js.
- Initial storage: SQLite for local prototype, PostgreSQL for deployed version.
- Authentication: add only when deploying beyond private/local use.

Validation:

- Create a task from the web UI.
- Answer a Manager clarification question.
- Observe status changes.
- Download or view the final report.
- Confirm mobile layout is usable.

## Agent Operating Model

### Current MVP

One Codex instance acts as Manager and internally performs the Researcher, Analyst, Writer, and Reviewer roles.

Benefits:

- Fastest to build.
- Lowest cost.
- Easy to debug.
- Best for validating workflow and report quality.

Limitations:

- Not truly parallel.
- Role independence is simulated.
- Long tasks can become context-heavy.
- Fine-grained progress tracking is limited.

### Target Architecture

Each role runs as a separate LLM call or worker.

Benefits:

- True role separation.
- Better status tracking.
- Easier web app integration.
- Role-specific model selection.
- Possible parallel execution.

Risks:

- Higher cost.
- More orchestration complexity.
- More failure modes.
- Requires stricter schemas, logging, and retry rules.

Decision:

- Continue with the single-Codex workflow until role prompts and schemas are stable.
- Split into independent LLM calls only after the role contracts are clear and testable.

## Quality And Acceptance Criteria

Every final report should satisfy these criteria:

- It answers the user's decision or reporting goal.
- It fits the target audience.
- It separates evidence, analysis, assumptions, and recommendation.
- It cites sources for current factual claims.
- It compares realistic options against explicit criteria.
- It shows major risks and caveats.
- It ends with practical next actions.

The system itself should satisfy these criteria:

- The skill validates successfully.
- CLI runs are reproducible.
- Role outputs are inspectable.
- Failure and revision states are visible.
- Later API/web layers can call the same core workflow without rewriting the agent logic.

## Test Plan

Skill validation:

```powershell
python "C:\Users\SINI\.codex\skills\.system\skill-creator\scripts\quick_validate.py" .
```

CLI validation:

```powershell
python .\scripts\research_team_cli.py "AI agent team web app development decision report" --title "AI Agent Team Web App" --out .\tmp-cli-test
```

Expected CLI output:

- A new task folder is created.
- The folder contains `task.json`, `draft.md`, `sources.md`, and `review.md`.
- `task.json` includes title, brief, status, roles, acceptance criteria, and artifact paths.

GitHub validation:

```powershell
git status --short
git log --oneline -3
git push
```

Expected GitHub state:

- `origin/main` contains `FINAL_WORK_PLAN.md`.
- The repository remains named `research-report-team`.

## Assumptions And Defaults

- The repository name remains `research-report-team`.
- Korean is used for user-facing explanations when the user works in Korean.
- English is used for file names, schemas, and prompt file names.
- OpenAI API calls are not added in the current documentation-only change.
- Web app development starts only after CLI and independent agent runner behavior are stable.
- File-based state is preferred until the API/web app phase.
- The initial web app target is private personal/team use, not a public SaaS product.

