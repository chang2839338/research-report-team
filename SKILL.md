---
name: research-report-team
description: Decision research and report-writing team workflow. Use when the user wants an AI team to clarify a decision goal, research a topic, compare options, draft a business or executive report, review evidence and logic, revise gaps, and deliver a decision-ready final document, including a Word .docx file when producing report artifacts.
---

# Research Report Team

## Operating Model

Core boundary sentence:

Manager contracts; Researcher extracts; Evidence Auditor gates; Analyst decides; Writer expresses; Reviewer audits; Revision Writer patches; Final Verifier gates; Publisher packages.

Core roles:
- Manager: produce `00_task_contract.json` and `00_task_brief.md`, or pause for clarification.
- Researcher: extract source-backed evidence, preliminary claims, numbers, gaps, and provenance.
- Evidence Auditor: decide which evidence is usable, caveated, excluded, blocked, or incomplete.
- Analyst: model the decision from audited evidence.
- Writer: produce the reader-facing draft and writer trace.
- Reviewer: audit the draft and emit a structured review decision.
- Revision Writer: apply required revision IDs only.
- Final Verifier: enforce the pre-publication gate.
- Publisher: deterministic system publication; no Codex call.

Temporary specialist roles may be added for domain-specific work, such as Market Expert, Technical Evaluator, Legal/Policy Checker, Financial Analyst, Risk Analyst, or Korean Executive Editor.

## Workflow

1. Clarify only when the goal, audience, scope, format, or decision criteria materially change the output.
2. Convert the request into `artifacts/00_task_contract.json` and `artifacts/00_task_brief.md`.
3. Run Researcher before analysis and keep stable `S#`, `C#`, and `N#` IDs.
4. Have Evidence Auditor produce `02_evidence_gate.json`; stop before analysis if it is blocked or incomplete.
5. Have Analyst produce decision frame, option evaluation, scenarios, recommendation, rollup, and `03_analysis_status.json`.
6. Have Writer produce both `04_draft.md` and `04_writer_trace.md`.
7. Have Reviewer produce `05_review_decision.json`, `05_review.md`, and `05_claim_audit.md`.
8. If the structured review decision is `targeted_revision` or `needs_revision`, run Revision Writer and produce `06_revision.md` plus `06_revision_trace.md`.
9. Have Final Verifier produce `07_final_verification.json`; stop if it blocks publication.
10. Publish deterministically to `08_final.md`, generate `08_final.docx`, and write `08_final_manifest.json`.

## Question Policy

Ask only questions that materially change the output. Prefer one focused question at a time when using this skill interactively.

Default recommended assumptions:
- Audience: decision maker or team lead.
- Output: concise decision brief in Markdown plus a Word `.docx` copy when writing artifacts locally.
- Depth: practical enough to support action, not exhaustive.
- Tone: professional, direct, Korean if the user writes in Korean.
- Evidence: cite sources for current or factual claims.

## Context Packet

Use `00_task_contract.json` and `00_task_brief.md` as the source of truth for role context. Role agents should receive only their prompt, acceptance criteria, and the prior artifacts required for their work.

## Word Output

When the workflow creates local artifacts, produce:
- `artifacts/08_final.md` for the auditable Markdown final report.
- `artifacts/08_final.docx` for the user-facing Word report.
- `artifacts/08_final_manifest.json` for selected source, hashes, final gate, caveats, and publication metadata.

The Markdown report is the auditable source of truth.

## Quality Gate

Before final delivery, verify:
- The document answers the user's decision or reporting goal.
- The recommendation follows from audited evidence.
- Key assumptions and uncertainty are visible.
- Important alternatives and risks are not hidden.
- Current factual claims are sourced.
- The final Markdown artifact has a matching Word `.docx` file when a local workspace is available.

Read these references only when needed:
- `references/roles.md` for detailed role responsibilities.
- `references/workflow.md` for the full team loop and state rules.
- `references/report-quality-rubric.md` for review scoring.
- `references/output-templates.md` for reusable report formats.
- `references/chatgpt-pro-workflow.md` for using this skill through ChatGPT Pro without API calls.
- `references/install-and-update.md` for installing or updating the skill from GitHub.
- `references/task-contract.md` for consistent task contracts and artifacts.
- `references/quality-checklist.md` for final report approval checks.
- `references/deferred-automation-criteria.md` for deciding when API, agent runner, or web app work is justified.
- `prompts/` for role-specific prompt files.
