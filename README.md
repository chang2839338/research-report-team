# Research Report Team

Local web app for running the research-report-team workflow through Codex.

## Run

```powershell
python .\scripts\research_team_server.py --port 8765
```

Open `http://127.0.0.1:8765` in a browser.

## Workflow

1. Enter a report title and brief.
2. Click `보고서 작업 실행`.
3. The server runs Codex role by role.
4. Each role stores only two files: `prompt 발송` in `prompts/` and `AI 회신` in `artifacts/`.
5. The final report is saved as `artifacts/05_final.md`.

Codex role runs default to a read-only sandbox. The server saves each final answer with `--output-last-message`, strips only outer Markdown fences, and does not persist duplicate reply transcripts.
