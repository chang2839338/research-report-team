# Research Report Team Design

## Concept

The app is a quiet operations console for Codex-based report production. It keeps each Agent's work auditable and prevents late-stage report drift by making Publisher a deterministic system step.

## Structure

- Left rail: report inputs and recent runs.
- Main header: report title and compact status.
- Progress strip: nine clickable workflow steps.
- Output area: one selected Agent output panel.
- Codex roles show a prompt tab plus artifact tabs.
- System Publisher has no prompt tab and shows final Markdown plus manifest tabs.
- Multi-artifact roles show every artifact declared by `contracts.py`.

## Workflow Contract

- Semantic work runs through `codex exec`, not direct OpenAI API calls.
- Multi-artifact responses use exact artifact markers and are split by the server.
- JSON sidecars are machine-readable gates for Manager, Evidence Auditor, Analyst, Reviewer, and Final Verifier.
- Publisher copies the verified final candidate to `08_final.md`, writes `08_final.docx`, and writes `08_final_manifest.json`.

## Interaction Rules

- Clicking a progress step selects that Agent.
- Running jobs update automatically by polling the run API.
- Runtime states include running, remediating, continuing with issues, publishing, completed, completed with unresolved issues, blocked, failed, cancelled, and needs clarification.
- Previous artifact inputs are hidden in prompt view and can be opened from their own Agent tabs.

## Storage Rules

- Save prompts in `prompts/`.
- Save AI replies and system publication files in `artifacts/`.
- Save exact Codex token usage in each `status.json` `agent_runs` entry.
- Save failure details in `error.log`.
- Preserve historical runs without migration.
