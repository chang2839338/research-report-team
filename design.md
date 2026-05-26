# Research Report Team Design

## Concept

The app is a quiet operations console for report production. It prioritizes progress visibility, compact controls, and direct inspection of what was sent to Codex and what came back.

## Structure

- Left rail: report inputs and recent runs.
- Main header: report title and one short status word.
- Progress strip: six clickable Agent steps. This is the only Agent navigation.
- Output area: final report plus selected Agent output.
- Agent output has only two views: `prompt 발송` and `AI 회신`.

## Visual Direction

- Warm paper canvas.
- Ink, sage, and clay neutrals.
- Thin borders, 8px radius, light shadows.
- No duplicate role tabs, no decorative status pills, no explanatory hero copy.

## Interaction Rules

- Clicking a progress step selects that Agent.
- Status labels are short: `대기`, `진행중`, `완료`, `실패`.
- Running jobs update automatically by polling the run API.
- When showing `prompt 발송`, previous artifact inputs are shown only as `# Input: artifacts/...` headers; their full bodies are omitted from the screen because they can be opened from the prior Agent step.
- User-facing labels should use the same concise Korean operations-console voice across buttons, empty states, status text, and panel labels.

## Storage Rules

- Save prompts in `prompts/`.
- Save AI replies in `artifacts/`.
- Do not save duplicate `responses/` files.
- Save failure details in `error.log`.
