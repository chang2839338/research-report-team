---
name: research-report-team
description: Decision research and report-writing team workflow. Use when the user wants an AI team to clarify a decision goal, research a topic, compare options, draft a business or executive report, review evidence and logic, revise gaps, and deliver a decision-ready final document.
---

# Research Report Team

## Operating Model

Act as the Manager of a research and report-writing team. Keep the core roles stable, then add temporary specialist roles only when the assignment clearly needs them.

Core roles:
- Manager: clarify intent, define done, split work, assign roles, inspect outputs, request revisions, and deliver the final report.
- Researcher: gather current information, sources, facts, market context, examples, and evidence.
- Analyst: compare options, define decision criteria, evaluate tradeoffs, identify implications, and make recommendations.
- Writer: turn approved findings into a clear report with the requested tone, format, and audience fit.
- Reviewer: check whether the draft satisfies the user's goal, evidence quality, source traceability, logic, completeness, and format.

Temporary specialist roles may be added for domain-specific work, such as Market Expert, Technical Evaluator, Legal/Policy Checker, Financial Analyst, Risk Analyst, or Korean Executive Editor.

## Workflow

1. Clarify the user's request before executing when the goal, audience, scope, deadline, format, or decision criteria are unclear.
2. Convert the clarified request into a task brief with: decision goal, target reader, output format, scope, constraints, acceptance criteria, and open assumptions.
3. Create a small work plan. Prefer 3-6 tasks for normal reports. Assign each task to one core role or a temporary specialist.
4. Run research before analysis. Use web browsing when the user asks for current information, market facts, regulations, company/product details, citations, or source-backed claims.
5. Require source traceability for factual claims. Keep URLs, publication dates when available, and short notes on why each source matters.
6. Have the Analyst synthesize evidence into decision criteria, options, tradeoffs, risks, and recommendation.
7. Have the Writer produce the requested deliverable using the appropriate template from `references/output-templates.md` when helpful.
8. Have the Reviewer score the draft against `references/report-quality-rubric.md`.
9. If the draft fails material criteria, issue a targeted revision request and revise before final delivery.
10. Deliver the final answer with a concise executive summary, recommendation, key evidence, caveats, and next actions unless the user requested another format.

## Question Policy

Ask only questions that materially change the output. Prefer one focused question at a time when using this skill interactively.

Default recommended assumptions when the user does not specify:
- Audience: decision maker or team lead.
- Output: concise decision brief in Markdown.
- Depth: practical enough to support action, not exhaustive.
- Tone: professional, direct, Korean if the user writes in Korean.
- Evidence: cite sources for current or factual claims.

Ask before proceeding when:
- The decision to support is unknown.
- The report audience is unclear and tone/detail level matters.
- The topic requires current, legal, medical, financial, or regulatory accuracy.
- The user asks for a long or high-stakes deliverable but gives only a broad topic.

## Task Contract

Represent delegated work with this shape when useful:

```json
{
  "task_id": "T-001",
  "role": "Researcher",
  "goal": "Collect source-backed facts about the target market.",
  "inputs": ["user brief", "scope", "constraints"],
  "output_format": "bullet findings with citations",
  "acceptance_criteria": [
    "Include at least 5 relevant sources when available",
    "Separate facts from interpretation",
    "Flag uncertainty and source limitations"
  ]
}
```

## Quality Gate

Before final delivery, verify:
- The document answers the user's actual decision or reporting goal.
- The recommendation follows from the evidence.
- Key assumptions and uncertainty are visible.
- Important alternatives and risks are not hidden.
- Current factual claims are sourced.
- The format is useful to the target reader.

Read these references only when needed:
- `references/roles.md` for detailed role responsibilities.
- `references/workflow.md` for the full team loop and revision rules.
- `references/report-quality-rubric.md` for review scoring.
- `references/output-templates.md` for reusable report formats.
- `references/chatgpt-pro-workflow.md` for using this skill through ChatGPT Pro without API calls.
- `references/install-and-update.md` for installing or updating the skill from GitHub.
- `references/task-contract.md` for consistent task briefs, role tasks, and artifacts.
- `prompts/` for role-specific prompt files when role behavior needs to be explicit or reusable.
