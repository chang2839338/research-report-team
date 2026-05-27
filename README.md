# Research Report Team

Local web app for running the research-report-team workflow through Codex.

This project does not call the OpenAI API directly. The server keeps using `codex exec` role by role, with the same workflow:

`Manager -> Researcher -> Analyst -> Writer -> Reviewer -> Final Manager`

## Run

```powershell
python .\scripts\research_team_server.py --port 8765
```

Open `http://127.0.0.1:8765` in a browser.

For higher quality research, pass the Codex model through the existing CLI option:

```powershell
python .\scripts\research_team_server.py --port 8765 --codex-model gpt-5
```

If `--codex-model` is omitted, Codex uses its configured default model.

## Research Artifacts

The Researcher still runs as one Codex role, but its response is split into four artifacts:

- `artifacts/01_research.md`: human-readable research memo.
- `artifacts/01_sources.md`: source ledger with URLs, publishers, dates, credibility, relevance, and limitations.
- `artifacts/01_claims.md`: claim evidence table with verification status.
- `artifacts/01_gaps.md`: unsupported claims, evidence gaps, conflicts, and follow-up searches.

The Researcher must include these exact markers in its final response:

```markdown
<!-- artifact: 01_research.md -->
<!-- artifact: 01_sources.md -->
<!-- artifact: 01_claims.md -->
<!-- artifact: 01_gaps.md -->
```

If any required section is missing or empty, the run fails and writes details to `error.log`.

## Workflow Notes

1. Enter a report title and brief.
2. Click `작업 실행`.
3. The server runs Codex role by role.
4. Prompts are saved in `prompts/`.
5. AI replies are saved in `artifacts/`.
6. Exact token usage from Codex is saved in `status.json`.
7. The final report is saved as `artifacts/05_final.md`.

The app writes UTF-8 files and sets Python subprocess encoding variables for Codex runs. Existing historical runs are preserved as-is; new runs should round-trip Korean text correctly.
