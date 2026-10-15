## Development process

Use this process only when I ask for it. I ask by name, for example "follow the development process" or "use the dev process". Without that, ignore this whole section and work normally.

Before anything else, check that these three skills are installed: `increments-plan`, `clean-code-implementation` and `code-review-full`. If any one is missing, abort early and tell me which.

### 1. Plan

- Before coding or writing, read the requirement. Confirm the expected outcome with me.
- Then hold a meeting between two planning subagents, both at high effort: one on opus, one on gpt-6.1-sol[1m]. They discuss the solution for the ticket together. You chair the meeting and do not plan yourself.
- Discuss for max 3 rounds (15 min time cap per round).
- Do not report to me while a planner is still working. If one planner finishes first, wait in the background for the other. Report only the consolidated result of the meeting.
- If you all agree, consolidate and write the final plan with the `increments-plan` skill. That skill is required. Don't follow `docs/plans/TEMPLATE.md` unless I say so.
- If you disagree after 3 rounds, tell me. Report each open point as a decision, with the full context the `increments-plan` skill requires: issue, cause, fix, why a decision, and each option with its pros and cons. Use plain words a 5-year-old can understand. This report is exempt from the 150-word limit.
- When I ask a question about a plan, always keep both planning subagents in the loop, so they may suggest things.
- After planning, show me the full link of the plan's local path and stop. Start implementation only after I explicitly approve the plan. No approval, no code.

### 2. Implement

Only the developer subagent changes code, including fixes for review findings and CI failures. The planning and review subagents never touch code.

Send the plan to a developer subagent. It must use the `clean-code-implementation` skill.

Developer model preference, in this order: sonnet (high), opus (medium). Use the first one available. Only use those models. If none is available, abort loudly and tell me which ones you tried.

The developer subagent must follow the `tdd` skill. It works the plan's test list in order. For every test it runs one loop: write the failing test, make it pass, refactor, then commit. One loop, one commit. It commits only when the suite is green, never on red. It does not batch several tests into one commit.

After implementation:

- Review the code with the `code-review-full` skill. It runs three checks: `code-review-do-what-it-claims`, `code-review-leaks` and `clean-code-implementation`.
- Start one subagent per check, in parallel. Each one loads only its own child skill and reviews only that category. Then collect all three reports.
- One subagent running `code-review-full` alone is also fine for a small diff.
- Don't use any other review skill (known case: `ship:review` — never use it unless asked).
- Model preference: gpt-6.1-sol[1m] > opus. Only use those models. If none is available, abort.
- Wait for the reviews.
- Verify every finding against the code and plan.
- Send verified critical findings to the developer subagent to fix.
- Repeat review and fixes until no critical findings remain.
- Treat nit findings as optional.

### 3. Ship

- Then create a ready PR.
- Babysit the PR until `ci / *` and `security / *` CI checks are green, and no more critical findings from prelint and betterreview in the PR.
- When babysitting the PR, don't ask subagents for code reviews. Only review before creating the PR.
- Send the PR to the merge queue after babysitting is finished.
- Then repeat the same loop for the next PR in the plan: code, reviews, babysitting, merge. Do this for every PR in the plan.

