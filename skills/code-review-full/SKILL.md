---
name: code-review-full
description: Full review of the current branch against main — runs the claim-check, the security/performance-leak review, and the clean-code check together. Use when the user asks for a full code review, a combined review, or just "review this branch" without specifying which kind.
---

# Code review: full

Run all three reviews of the current branch against `main`, then combine the
results. This is the index skill; it does not duplicate their checks.

## Steps

1. Load and run `code-review-do-what-it-claims` — does the diff do what it
   claims.
2. Load and run `code-review-leaks` — security and performance leaks in the
   changed files.
3. Load and run `clean-code-implementation` against the same diff — check
   every added or changed line for its rules (verb function names, function
   size, self-documenting names over comments, helper ordering, and the
   wider maintainability habits it indexes). Only the lines the diff touched
   are in scope; do not flag a pre-existing violation the diff did not add
   to or change.
4. All three checks scope themselves to `git diff --name-only main...HEAD`.
   Do not widen or narrow that scope between them.

## Report

Three sections, one per skill, each in that skill's own report format. End
with one line: overall verdict (ship / fix first / needs discussion).
