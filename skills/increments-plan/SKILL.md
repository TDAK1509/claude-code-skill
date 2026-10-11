---
name: increments-plan
description: Plan a task as a sequence of small, single-responsibility PRs, each one a working, testable, revertible step toward an outcome. Every PR carries an outcome list — the steps someone runs to confirm it works — and its tests in the order they get written, one tdd loop each. It starts from a map of the existing behavior, updated with the request. Use when planning or scoping multi-step work, when a task looks too big for one PR, when the user asks for a phased or incremental plan, or when the user asks how to break work into pull requests.
---

# Increments plan

A plan is a sequence of PRs, not a design document. State the outcome you want,
not the solution you have already decided on. Let the steps discover the
solution.

The plan goes to a developer with zero context. They have not seen the ticket,
this conversation, or the code you read. They only execute the plan. So the plan
must be self-sufficient: every PR, every outcome, and every test must make sense
to a reader who has nothing else. See "Write for a reader with zero context"
below.

## How to plan

Think in this order. Do not skip a step, and do not start a later step before
the one above it is done.

1. **Research the existing behavior.** Read the code around the request: the
   entry points a user hits, the data it reads and writes, the paths it takes
   today. Read until you know what the system does now, not what it probably
   does.
2. **Draw the map of today.** Sketch how the behavior works now, as boxes and
   arrows in plain words: who acts, what happens, where the data goes. No code
   details — no file, class, or function names. If you cannot draw it, you have
   not read enough. Go back to step 1.
3. **Update the map with the request.** Redraw the same map as it must be when
   the request is done. Mark every box and arrow that is new, changed, or
   removed. Everything unmarked stays as it is.
4. **Plan from the marks.** Each marked part is a piece of work. Group the marks
   into PRs, order them, and write each PR as the rest of this skill describes.
   A PR that touches no mark is out of scope. A mark that no PR covers is a
   gap.

Task: CSV export, next to an existing PDF export.

Today:

```
user → orders page → [Export PDF] → export route → reads order rows → PDF file → download
```

Requested:

```
user → orders page → [Export PDF] → export route → reads order rows → PDF file → download
                   → [Export CSV]* → export route (format choice)* → reads order rows → CSV file* → download
```

Three marks: the CSV button, the format choice on the route, and the CSV
file. The order rows and the download stay untouched. The plan covers the three
marks and nothing else.

The maps are your thinking, not the plan. They do not go into the plan output.

## Not optional

Every step in the plan is a PR. Every PR ships something that works. A step
that only sets up for a later step, with nothing observable on its own, is not
a step — merge it into the step that makes it real.

## Start from the outcome, not the solution

Write one sentence: what should be true when this is done. Not how it will be
built.

- "Users can export their data as CSV" is an outcome.

Bad examples: [Solution instead of outcome](references/bad-examples.md#solution-instead-of-outcome).

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

Bad examples: [Outcomes nobody can perform](references/bad-examples.md#outcomes-nobody-can-perform).

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
- Possible in the real app. Every page, button, label, and message must exist
  in the code today, or this PR adds it. See "Every step must be possible in
  the real app" below.

When a step is invisible by design — a flag-guarded path, a new column nothing
reads yet — the outcome is the flag or the query, not the feature. "Set
`NEW_EXPORT=1`. Open the export page. It shows the same rows as today." An
invisible step still has a way to check it, or it is not a step.

### Every step must be possible in the real app

An outcome is a manual test, so a real person must be able to perform every
bullet in the app as it is. Do not imagine the app. Check it.

Before you write a bullet, find in the code where that action exists today, or
where this PR adds it:

- The page: find its route. Do not name a page that has no route.
- The button, link, menu, or field: find it on that page. Use its real label.
- The way the user gets there: find the navigation that leads to the page. Do
  not assume a link that is not there.
- The data the step needs: say how it exists — the user creates it in an
  earlier bullet, or it already exists in the environment. Do not assume a
  seed, an admin tool, or a test account that is not there.
- The result: find where it shows — the message text, the list, the file, the
  status code. Use the real text.

Bad examples: [Steps from an imagined app](references/bad-examples.md#steps-from-an-imagined-app).

When a step has no way to be performed through the app — a background job, a
webhook, a failure no user can cause — do not invent a user action for it. Name
the real tool someone uses to cause it, such as a command, a request to an
endpoint, or a log line to read. If no such tool exists, say so in the
terminal. Do not write a step nobody can execute.

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

Read [references/bad-examples.md](references/bad-examples.md) before you write
the plan. It shows the mistakes plans make most often, and how to fix each one.

For each PR, state:

1. **Outcome** — the definition of done as a short list of steps, each one an
   action and the result it produces. See "The outcome is a test someone can
   run" above.
2. **Solution** — the approach in two or three sentences, then the tests this
   PR adds, in the order they get written. Each test is one `tdd` loop. See
   "The solution" below.
3. **Revert cost** — what reverting this PR alone does to production: nothing,
   or name the one thing.
4. **Evidence** — the file, function, or existing pattern you read that this
   step's approach is based on. Name it (`path/to/file.ts:42`, the test that
   already covers this path, the sibling feature that does the same thing).
   If no such evidence exists because nothing like it is in the repo yet, say
   so instead of inventing a source.

## The solution

Two parts: a brief explanation, then the tests in order. Neither holds code.

### The explanation

Two or three sentences in plain terms. What changes, why this way and not
another, and what stays untouched. A reader who has not opened the repository
must be able to follow it.

"CSV export rides on the route that already serves PDF export, because both read
the same order rows. Only the response format differs. Leave the download UI
alone — a later PR wires it up."

### The tests, in order

The coding agent builds the PR with the `tdd` skill, one loop per test:

```
write the failing test → make it pass → refactor → commit
```

So the plan lists the tests in the order they get written. That order is the
implementation order, and it must be correct: each test has to be writable and
passable with only the tests above it in place. A test that needs a later test's
code sits in the wrong place — move it down.

Each test has a heading line and three bullets:

```
1. <Side> (<test type>): <goal of the test in one sentence>

   - Setup: <the state that exists before the test runs>
   - Input: <the one action or request the test makes>
   - Expected: <the one result the test checks>
```

- **Side** is `Backend` or `Frontend`.
- **Test type** is `unit`, `integration`, or `e2e`.
- **Goal** says in one sentence what the test proves.

Task: CSV export.

1. Backend (integration): The export holds one row per order.

   - Setup: An account with three orders.
   - Input: Run the export for that account.
   - Expected: The file holds a header row and three rows.

2. Backend (integration): The export of an empty account holds only the header.

   - Setup: An account with no orders.
   - Input: Run the export for that account.
   - Expected: The file holds the header row and nothing else.

3. Backend (unit): A comma in a value does not split the column.

   - Setup: An order whose customer name is `Smith, Jane`.
   - Input: Format that order as a CSV row.
   - Expected: `Smith, Jane` stays in one column.

4. Backend (integration): A signed-out visitor cannot export.

   - Setup: No signed-in user.
   - Input: Request the export URL.
   - Expected: The response is `401`.

5. Frontend (e2e): The Export button downloads the file.

   - Setup: A signed-in user with three orders, on the orders page.
   - Input: Click Export.
   - Expected: The browser downloads a `.csv` file.

Five tests, five loops, five commits. The PR is done when every test in the list
is green and committed.

Rules for the list:

- Every test uses the heading line and the three bullets: Setup, Input,
  Expected.
- Every heading names the side and the test type.
- One action in Input. One result in Expected. See "One case per test" below.
- In writing order. Each test depends only on the ones above it.
- Name the condition that makes the case different — an empty list, a comma in
  the data, a missing permission — not just "the happy case" and "the error
  case".
- No code: no test file names, no function or helper names, no framework, no
  assertion syntax. The coding agent decides all of that.
- Only tests this PR adds. A behaviour a later PR introduces is tested in that
  PR.
- If a step genuinely adds no test — a pure rename, a config move — say that
  and say why, instead of inventing one.
- Readable with zero context. See "Write for a reader with zero context" below.

### Write for a reader with zero context

The developer who runs the plan knows nothing you know. Each test must stand on
its own, read by someone who has never seen the ticket, the conversation, or the
code.

Readable without context:

```
1. Backend (integration): An uploaded file gets a virus scan.

   - Setup: A user attaches a `.pdf` to a chat message in Slack.
   - Input: The file finishes uploading.
   - Expected: A virus scan job is created for that message.
```

Rules:

- Use plain words for every thing the test names. Say what it is, not what you
  called it while you planned.
- No private shorthand: no nicknames, no ticket terms, no "the bug", "the
  flow", "the new path", "as discussed".
- No references to other tests. "Same as above" and "same platform" force the
  reader to piece the test together. Write each test in full, even when it
  repeats words from the test above.
- No references outside the plan. If a test depends on a fact from the ticket
  or the code, write the fact into the test or the explanation.
- Concrete values beat vague ones: "three orders", "a name with a comma",
  "status `401`", not "some data", "bad input", "an error".

Test it: read the test as if this plan were the only thing you had. If you must
ask "which one?" or "what does that mean?", rewrite it.

Bad examples: [Test that needs context](references/bad-examples.md#test-that-needs-context).

### One case per test

A test checks one case. An "or" or an "and" in Setup, Input, or Expected hides
several tests in one. When that test goes red, nobody knows which case broke.

Split it, one test per case. Each one fails on its own, so each gets its own
loop and its own commit. The same holds for a list of file types, status codes,
roles, environments, or any other "A, B and C" in a test.

Bad examples: [Test with an "or"](references/bad-examples.md#test-with-an-or),
[Test with too many "and"](references/bad-examples.md#test-with-too-many-and).

### Neither part holds code

Both parts answer none of these: which classes exist, what the functions are
called, what the signatures are, which pattern the code follows. The coding
agent decides all of that once it has read the code.

Bad examples: [Solution that holds code](references/bad-examples.md#solution-that-holds-code).

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

- Did you draw the map of today and the requested map, and does every mark
  belong to a PR?
- Does every step ship something true in production, not just true in the
  repo?
- Can you stop after any step and leave production working?
- Can you revert any single step without touching the others?
- Is any step describable only with "and"? Split it.
- Does every step name the evidence its approach came from, or say plainly
  that none exists?
- Does every step carry an outcome list someone can perform on the day it
  merges, with every page, button, and message checked against the code?
- Does every step explain its approach and list the tests it adds, in writing
  order, one case per test, each with a side, a test type, Setup, Input, and
  Expected, without naming the code that will implement it?
- Can a developer with zero context read every outcome and every test and know
  what to do, without the ticket, this conversation, or a "same as above"?
- Does the plan contain any unresolved "decide: X" or open question? If so,
  ask in the terminal and resolve it before the plan is done.

Eight "yes" and one "no unsplit step" and one "no unresolved question" and the
plan is ready.
