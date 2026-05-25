# Deferred Automation Criteria

Use this document to decide when `research-report-team` should move beyond the ChatGPT Pro skill workflow into API calls, an independent agent runner, or a web app.

Current default: stay with **ChatGPT Pro + Codex Skill + local CLI workspace**.

## Decision

Do not build API execution, an independent agent runner, or a web app yet.

Revisit automation only after the skill workflow has been used enough to show real repetition, clear bottlenecks, and value that justifies extra cost and complexity.

## Why The Default Is Conservative

The current project is still validating:

- role prompts,
- task contracts,
- report formats,
- quality checks,
- local file workflow,
- actual user habits.

API and web app work should not begin until these foundations are stable. Otherwise, the project may automate the wrong workflow.

## API Usage Gate

Start considering API calls only when most of these are true:

- The workflow is used at least 8-10 times per month.
- Manual copy/paste between ChatGPT and local files is a real productivity cost.
- The same role sequence is repeated often enough to automate.
- The user accepts separate API billing.
- The output format and quality checklist are stable.
- There is a clear need to run tasks without manually opening a ChatGPT chat.

Do not use API calls just because they are technically possible.

## Independent Agent Runner Gate

Start considering an independent agent runner only when:

- Role prompts have produced consistent results across several real tasks.
- The CLI workspace structure is stable.
- Each role artifact has a predictable shape.
- Reviewer feedback reliably identifies revision needs.
- A bounded retry loop is defined.
- Logs and failure states are needed for real work.

The first runner should be sequential, not parallel. Parallel execution should wait until sequential behavior is reliable.

## Web App Gate

Start considering a web app only when most of these are true:

- The user needs to submit tasks away from the development PC.
- Mobile or remote status checks are genuinely useful.
- Multiple reports or projects need browsing and search.
- Reports need to be shared with other people.
- Background execution has enough value to justify server hosting.
- Authentication and data privacy needs are understood.

Do not build a web app only to make the project look complete. Build it when browser access changes the usefulness of the workflow.

## Cost Gate

Before API or web app work begins, write down:

- expected monthly task count,
- expected average report length,
- which roles would use API calls,
- estimated monthly API cost,
- expected time saved,
- whether the saved time is worth the cost.

If the answer is unclear, continue using ChatGPT Pro manually.

## Automation Value Checklist

Automation is probably worth testing when:

- [ ] The same workflow is repeated often.
- [ ] Manual steps are slowing the user down.
- [ ] The desired output shape is stable.
- [ ] The user wants tasks to run while away from the keyboard.
- [ ] Status tracking matters.
- [ ] API cost is acceptable.

Automation is probably premature when:

- [ ] The workflow is still changing frequently.
- [ ] The user is still learning what reports should look like.
- [ ] Most tasks are one-off and unique.
- [ ] Manual ChatGPT Pro usage is still fast enough.
- [ ] Cost control is more important than automation.

## Recommended Future Sequence

If the gates are met later, proceed in this order:

1. Add file-based independent agent runner.
2. Run one role at a time sequentially.
3. Add logs and bounded retry behavior.
4. Add API calls only for the roles that need automation.
5. Add a local API server.
6. Add a private web UI.
7. Consider mobile-friendly access.

## Current Project Status

Current status: **defer API, agent runner, and web app work**.

Next best work:

- improve ChatGPT Pro usage guidance,
- refine role prompts,
- improve CLI workspace organization,
- gather real examples,
- review actual usage after several reports.

