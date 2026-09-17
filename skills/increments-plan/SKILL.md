---
name: increments-plan
description: Plan a task as a sequence of small, single-responsibility PRs, each one a working, testable, revertible step toward an outcome. Every PR carries an outcome list — the steps someone runs to confirm it works. Use when planning or scoping multi-step work, when a task looks too big for one PR, when the user asks for a phased or incremental plan, or when the user asks how to break work into pull requests.
---

# Increments plan

A plan is a sequence of PRs, not a design document. State the outcome you want,
not the solution you have already decided on. Let the steps discover the
solution.

## Not optional

Every step in the plan is a PR. Every PR ships something that works. A step
that only sets up for a later step, with nothing observable on its own, is not
a step — merge it into the step that makes it real.

## Start from the outcome, not the solution

Write one sentence: what should be true when this is done. Not how it will be
built.

- "Users can export their data as CSV" is an outcome.
- "Add an `ExportService` with a `CsvFormatter` strategy" is a solution you
  have not tested yet. Do not write this in the plan.

A detailed upfront design is a guess about code you have not changed yet. The
PRs are how you find out if the guess holds. If step 2 reveals step 4 was
wrong, that is the plan working, not the plan failing.

## Each PR is a real step, not a fragment

For every PR in the plan, answer:

- **What can a reviewer see work?** A passing test, a new path a user can hit,
  a flag they can flip, a script they can run. "Trust me, step 4 uses this" is
  not an answer. Write the answer as the outcome list — see "The outcome is a
  test someone can run" below.
- **What breaks if this ships alone and nothing after it ever lands?** The
  answer must be "nothing in production." A half-built abstraction with no
  caller is not safe to stop at.
- **How does someone revert just this PR?** If reverting it requires also
  reverting a later PR, they are not two PRs — merge them or reorder them.

## The outcome is a test someone can run

Every PR carries its outcome as a short list of steps. This is the definition of
done. A PR without it is not planned, it is only described.

Write it as a manual test. Each bullet is one action and the result it produces.
Someone performs the list top to bottom, the day the PR merges.

Task: email and password login.

- Open the login page.
- Type a registered email and its password. Submit.
- The signed-in page loads.
- Type a wrong password. Submit.
- The page shows `Invalid email or password` and stays on the login page.

Task: CSV export.

- Open the orders page.
- Click Export.
- A `.csv` file downloads.
- The file holds a header row and one row per order.

Task: a rate limiter on the send endpoint.

- Send ten requests in one minute. Each returns `200`.
- Send an eleventh in the same minute. It returns `429`.
- Wait a minute. The next request returns `200`.

These are not outcomes:

- "The tests pass." Which test, and what does it prove.
- "The code compiles." That is not an outcome.
- "`ExportService` is added." That is the solution, not the effect.
- "Export works end to end." Nobody can perform that sentence.

Rules for the list:

- One action per bullet. Short and direct.
- Three to six bullets. More means the PR does more than one thing.
- In order. The reader follows them like a manual test.
- In the language of the person using the system, not the language of the code.
- Performable the day the PR merges. If a bullet needs a later PR, this step is
  a fragment. Merge it forward or reorder.
- Name what changes: a page, a file, a status code, a row in a table, a log
  line.
- Cover the failure the change is about, not only the happy path.

When a step is invisible by design — a flag-guarded path, a new column nothing
reads yet — the outcome is the flag or the query, not the feature. "Set
`NEW_EXPORT=1`. Open the export page. It shows the same rows as today." An
invisible step still has a way to check it, or it is not a step.

## Order steps so production never breaks

- Land the parts that do nothing yet before the parts that turn them on.
  Behind a flag, behind a branch never taken, behind a caller that does not
  exist yet — all fine, as long as the PR itself is inert until wired up.
- Do the risky or uncertain part early, in its smallest form, so a wrong
  guess is cheap to find and cheap to revert. Do not save the riskiest step
  for last.
- Never write a step that depends on a later step to be correct. Each step
  depends only on the ones before it.

## Size each PR down

- One responsibility per PR. If describing a step needs "and", it is two
  steps.
- Prefer more, smaller PRs over fewer, larger ones. A PR too small to review
  is rare; a PR too large to review is common.
- A step that touches many files for one mechanical reason (a rename, a
  type change propagating outward) can stay one PR — the risk is the reason
  it exists, not its size in lines.

## Write the plan

For each PR, state:

1. **Outcome** — the definition of done as a short list of steps, each one an
   action and the result it produces. See "The outcome is a test someone can
   run" above.
2. **Solution** — two or three sentences on the approach in plain terms. What
   changes, why this way, and what stays untouched.
3. **Solution map** — a map of the change: which parts of the system take
   part, how data or control moves between them, and which parts this step
   must not touch. Draw it as a diagram when the flow has more than two hops.
4. **Revert cost** — what reverting this PR alone does to production: nothing,
   or name the one thing.
5. **Evidence** — the file, function, or existing pattern you read that this
   step's approach is based on. Name it (`path/to/file.ts:42`, the test that
   already covers this path, the sibling feature that does the same thing).
   If no such evidence exists because nothing like it is in the repo yet, say
   so instead of inventing a source.

## The solution

The solution has two parts: a brief explanation, then a map. Neither holds code.

### The explanation

Two or three sentences in plain terms. What changes, why this way and not
another, and what stays untouched. A reader who has not opened the repository
must be able to follow it.

"CSV export rides on the route that already serves PDF export, because both read
the same order rows. Only the response format differs. Leave the download UI
alone — a later PR wires it up."

### The map

The map is the vision, not the implementation. It shows the pieces and the flow
between them, so a reader sees the whole shape before any code exists.

Draw it when the flow has more than two hops:

```
Browser ──GET /export?format=csv──▶ Export route ──▶ Row builder ──▶ CSV response
                                          │
                                          └──▶ PDF path, untouched
```

Write it as prose when the shape is simple: "The export route grows a second
format branch. The PDF path and the download UI stay as they are."

Either form answers the same three questions:

- Which parts of the system take part?
- How does data or control move between them?
- Which parts must this step leave alone?

### Neither part holds code

Both parts answer none of these: which classes exist, what the functions are
called, what the signatures are, which pattern the code follows. The coding
agent decides all of that once it has read the code.

- Not a solution: "Add an `ExportService` with a `CsvFormatter` strategy and a
  `formatRow()` helper." That is code, and the code has not been read yet.

Do not write implementation detail beyond what the outcome and this solution
require.

## Unclear points go to the terminal, not the plan

The plan holds only decided points. If a step needs a decision or approval
you do not have — a design choice, a scope call, an ambiguous requirement —
stop and ask in the terminal before writing that step. Do not write
"decide: X", a question, or an open item into the plan itself.

Once the answer comes back, write the step as decided. If the ticket is too
ambiguous to plan safely even after asking, say so in the terminal instead of
producing a plan full of placeholders.

A step's outcome and approach must trace back to something you actually read
in the repository or the ticket, or to an answer you were given, not to an
assumption about how the codebase probably works. Evidence is what separates
"the outcome I chose" from "the outcome I guessed."

## Before you finish

- Does every step ship something true in production, not just true in the
  repo?
- Can you stop after any step and leave production working?
- Can you revert any single step without touching the others?
- Is any step describable only with "and"? Split it.
- Does every step name the evidence its approach came from, or say plainly
  that none exists?
- Does every step carry an outcome list someone can perform on the day it
  merges?
- Does every step explain its approach and map the change, without naming the
  code that will implement it?
- Does the plan contain any unresolved "decide: X" or open question? If so,
  ask in the terminal and resolve it before the plan is done.

Six "yes" and one "no unsplit step" and one "no unresolved question" and the
plan is ready.
