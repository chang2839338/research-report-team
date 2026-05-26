# Install And Update Guide

Use this guide to install or update `research-report-team` on a PC.

## Recommended Setup

The skill should live in the Codex skills folder:

```text
C:\Users\SINI\.codex\skills\research-report-team
```

The GitHub repository is:

```text
https://github.com/chang2839338/research-report-team
```

## First-Time Install On This PC

If the skill folder does not exist yet, run this from PowerShell:

```powershell
git clone https://github.com/chang2839338/research-report-team.git "$env:USERPROFILE\.codex\skills\research-report-team"
```

Then confirm the files exist:

```powershell
Get-ChildItem "$env:USERPROFILE\.codex\skills\research-report-team"
```

You should see:

- `SKILL.md`
- `references/`
- `scripts/`
- `agents/`

## Update An Existing Install

If the skill is already installed, run:

```powershell
cd "$env:USERPROFILE\.codex\skills\research-report-team"
git pull
```

This downloads the latest version from GitHub.

## Install Into A Separate Working Folder

For development work, keep a normal repo checkout somewhere convenient:

```powershell
git clone https://github.com/chang2839338/research-report-team.git
```

Use this development checkout for editing, committing, and pushing changes.

Use the `.codex\skills` copy for actual skill discovery by Codex.

## Validate The Skill

Run the validator from the repo root:

```powershell
python "C:\Users\SINI\.codex\skills\.system\skill-creator\scripts\quick_validate.py" .
```

Expected result:

```text
Skill is valid!
```

## Test The CLI

From the repo root:

```powershell
python .\scripts\research_team_cli.py "AI agent team 업무 방식 의사결정 보고서" --title "AI Agent Team Decision Brief"
```

Expected result:

- A new timestamped folder appears under `runs`, such as `runs/20260525_1338`.
- The folder includes `task.json`, `status.json`, `sources.md`, `prompts/`, and `artifacts/`.
- `prompts/` includes numbered Manager, Researcher, Analyst, Writer, and Reviewer prompt files with task context.
- `artifacts/` includes `00_task_brief.md` through `05_final.md`, plus `05_final.docx`.

After testing, delete the temporary folder if it is not needed.

## GitHub Login For Publishing Changes

Reading and using the skill does not require GitHub login after the files are installed.

Publishing changes to GitHub does require login. If needed, run:

```powershell
gh auth login -h github.com
gh auth status
```

Choose:

```text
GitHub.com
HTTPS
Login with a web browser
```

If an old token causes problems, clear it in the current PowerShell session:

```powershell
$env:GITHUB_TOKEN=$null
$env:GH_TOKEN=$null
gh auth status
```

## Common Problems

### Git says the repository has dubious ownership

This can happen when a sandbox or a different Windows user created the folder.

Fix it for this repo only:

```powershell
git config --global --add safe.directory "C:/Users/SINI/OneDrive/Desktop/agent group/research-report-team"
```

### Korean text looks broken in PowerShell

The file may still be fine. Read it as UTF-8:

```powershell
Get-Content .\docs\issue-notes\github-issues-ko.md -Encoding UTF8
```

### Codex does not seem to discover the skill

Check that `SKILL.md` is directly inside:

```text
C:\Users\SINI\.codex\skills\research-report-team\SKILL.md
```

If the repo was cloned into a nested folder by mistake, move the inner `research-report-team` folder so `SKILL.md` is at the path above.

