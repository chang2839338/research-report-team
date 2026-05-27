# Research Report Team Design

## Concept

The app is a quiet operations console for Codex-based report production. It keeps the existing role workflow, but makes the Researcher output auditable before downstream analysis and writing.

## Structure

- Left rail: report inputs and recent runs.
- Main header: report title and one short status word.
- Progress strip: six clickable Agent steps.
- Output area: one large selected Agent output panel.
- Most Agents have two views: `프롬프트` and `AI 응답`.
- Researcher has five views: `연구 메모`, `출처`, `주장 검증`, `공백/리스크`, and `프롬프트`.
- The final report is not shown in a separate panel. Select the `Final` step and open `AI 응답` to inspect `artifacts/05_final.md`.

## Research Contract

- The Researcher runs through `codex exec`, not a direct OpenAI API call.
- The Researcher returns one Markdown message with artifact markers.
- The server splits that message into `01_research.md`, `01_sources.md`, `01_claims.md`, and `01_gaps.md`.
- Analyst, Writer, Reviewer, and Final Manager receive the relevant research artifacts as normal prior inputs.

## Visual Direction

- Warm paper canvas.
- Ink, sage, and clay neutrals.
- Thin borders, 8px radius, light shadows.
- No duplicate role tabs, no decorative status pills, no explanatory hero copy.

## Interaction Rules

- Clicking a progress step selects that Agent.
- Status labels are short: `대기`, `진행 중`, `완료`, `실패`.
- Running jobs update automatically by polling the run API.
- The selected Agent panel header shows the exact completed-run token total for that Agent.
- When showing `프롬프트`, previous artifact inputs are shown only as `# Input: artifacts/...` headers; their full bodies are omitted from the screen because they can be opened from the prior Agent step.

## Storage Rules

- Save prompts in `prompts/`.
- Save AI replies in `artifacts/`.
- Save exact Codex token usage in each `status.json` `agent_runs` entry.
- Do not save duplicate `responses/` files.
- Save failure details in `error.log`.
- Preserve historical runs without migration.
