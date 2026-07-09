# ChatGPT Pro Workflow

Use this guide when running `research-report-team` through ChatGPT Pro and Codex without separate API calls.

## Purpose

This workflow lets a user run a research and report-writing team from a normal ChatGPT/Codex chat. One Codex instance acts as the Manager and performs the Researcher, Analyst, Writer, and Reviewer roles in sequence.

This is the recommended near-term workflow because ChatGPT Pro subscription usage and API usage are billed separately. This workflow is designed to avoid API calls unless the user later decides automation is worth the extra cost.

## What This Workflow Does

- Clarifies the user's decision or reporting goal.
- Splits the work into research, analysis, writing, and review.
- Produces a decision-ready report.
- Uses citations when current facts or external claims matter.
- Keeps API-based automation deferred.

## What This Workflow Does Not Do

- It does not run independent background agents.
- It does not call the OpenAI API.
- It does not run a web app.
- It does not automatically save every ChatGPT answer into local files.

The user can still copy final outputs into the local task workspace created by the CLI.

## Recommended Chat Start Prompt

Copy this into a new ChatGPT/Codex chat when starting a task:

```text
Use the research-report-team skill.

Act as the Manager of a decision research and report-writing team.
First clarify my goal with only the questions that materially affect the output.
Then split the work into Researcher, Analyst, Writer, and Reviewer tasks.
Use source-backed evidence for current factual claims.
Review the draft against the quality rubric before final delivery.

My request:
[paste the decision or report request here]
```

## Short Korean Starter Prompt

```text
research-report-team 스킬을 사용해줘.

너는 의사결정 리서치/보고서 작성팀의 팀장이다.
먼저 결과물에 영향을 주는 핵심 질문만 하고,
목표가 명확해지면 Researcher, Analyst, Writer, Reviewer 역할로 나누어 진행해줘.
최신 사실이나 외부 정보는 출처를 붙이고,
최종 답변 전에 품질 기준으로 검수해줘.

내 요청:
[여기에 업무 지시를 붙여넣기]
```

## Standard Operating Flow

1. Start a new ChatGPT/Codex chat.
2. Paste the starter prompt.
3. Add the actual decision or report request.
4. Let the Manager ask clarifying questions.
5. Answer the questions.
6. Let the team produce research, analysis, draft, review, and final report.
7. Copy the final report or important intermediate outputs into the local workspace if needed.

## When To Ask For Sources

Ask for sources when the work involves:

- Current market information.
- Company, product, or competitor claims.
- Regulations, policy, legal, medical, or financial topics.
- Prices, dates, statistics, or benchmarks.
- Any claim the user may need to defend in a real decision meeting.

Example:

```text
For factual claims, include source links and briefly explain why each source matters.
```

## When To Start A New Chat

Start a new chat when:

- The topic changes substantially.
- The previous chat became too long.
- The report needs a clean context.
- You want to reuse the same workflow for a separate decision.

Continue the same chat when:

- You are revising the same report.
- You are answering the Manager's clarification questions.
- You are asking the Reviewer to check the same draft.

## Saving Outputs Locally

Use the CLI to create a local workspace:

```powershell
python .\scripts\research_team_cli.py "your report request" --title "short title"
```

Then copy useful outputs into the generated files:

- `artifacts/00_task_brief.md`: shared context packet and task contract.
- `artifacts/01_research.md`: research findings.
- `artifacts/02_analysis.md`: option comparison and recommendation logic.
- `artifacts/03_draft.md`: report draft.
- `artifacts/04_review.md`: Reviewer feedback.
- `artifacts/05_final.md`: final report.
- `artifacts/05_final.docx`: Word copy of the final report.
- `sources.md`: source links and notes.
- `task.json`: task metadata created by the CLI.
- `status.json`: lightweight progress notes.

Start from `prompts/01_manager.md` when pasting task context into ChatGPT Pro.

## Practical Tips

- Ask for a decision brief when the goal is choosing between options.
- Ask for a research memo when the goal is understanding a topic.
- Ask for an executive report when the result will be shared with leadership.
- Tell the Manager the audience, deadline, desired length, and decision criteria when you know them.
- If the answer feels generic, ask the Reviewer to find missing evidence, weak logic, and unclear recommendations.

## Terms

- Skill: a reusable instruction set that teaches Codex how to handle a specific workflow.
- Manager: the role that clarifies the goal, assigns work, checks quality, and delivers the final answer.
- Researcher: the role that gathers evidence and sources.
- Analyst: the role that compares options and explains tradeoffs.
- Writer: the role that turns findings into a readable report.
- Reviewer: the role that checks whether the report is good enough.
- API: a programmatic way to call a model. It can create separate usage-based cost.
- CLI: a command-line tool that runs from PowerShell or a terminal.

