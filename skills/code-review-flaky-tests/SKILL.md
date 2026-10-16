---
name: code-review-flaky-tests
description: Review the current branch's diff against main for tests that can pass or fail without a code change — only in the changed files. Use when the user asks to review a PR, review changes, check for flaky tests, or check that new tests are deterministic.
---

# Code review: flaky tests

Compare the current branch against `main`. Examine only the changed files.
Look for tests that can pass on one run and fail on the next with no code
change. Not style, not coverage.

## Steps

1. List changed files only:
   ```bash
   git diff --name-only main...HEAD
   ```
2. Keep the test code from that list: test files, fixtures, factories, test
   helpers, test setup and teardown, and test config. Do not scan files outside
   this list.
3. Read the full diff for those files:
   ```bash
   git diff main...HEAD -- <file> ...
   ```
   Only lines the diff added or changed are in scope. Do not flag a
   pre-existing flaky test the diff did not touch.
4. Check each added or changed test for time and randomness:
   - Reads the real clock (`now`, today's date, the current timezone) instead
     of a frozen or injected time. Breaks at midnight, month end, a DST change,
     or on a CI machine in another timezone.
   - Uses random values without a fixed seed.
   - Waits a fixed time (`sleep`, `setTimeout`, a hard-coded wait) instead of
     waiting for a condition.
   - Asserts a duration or timeout that a slow CI machine can miss.
5. Check each added or changed test for order and shared state:
   - Depends on another test running first, or on data another test leaves.
   - Changes global, module, class, or environment state and does not restore
     it. A mock, a spy, an env var, or a patched function that outlives the
     test.
   - Writes rows, files, or cache entries and does not clean them up.
   - Uses fixed IDs, emails, ports, or file paths that collide when tests run
     in parallel.
   - Asserts the order of a result that has no defined order: a query with no
     `ORDER BY`, a set, a map, a directory listing, parallel tasks.
6. Check each added or changed test for concurrency and the outside world:
   - Does not await an async call, a promise, or a background job before it
     asserts.
   - Races two tasks, threads, or requests with no synchronization.
   - Calls a real network service, third-party API, or external process
     instead of a stub.
   - Depends on the machine: locale, OS path separator, installed tools, file
     system case, screen size.
   - Compares floating point values with exact equality.
7. For frontend and e2e tests, also check:
   - Selects an element before it renders, or during an animation, with no
     wait for it to be visible.
   - Uses a selector that changes with content or layout, such as a list
     index or generated class name.
8. Ignore correctness-vs-claim, security, performance, and naming/style — that
   is a different skill's job.

## Report

List each finding as: file:line, one-line description, the condition that
makes it fail (for example "fails after 23:00 UTC" or "fails when run after
`test_x`"). If nothing found, say so plainly. Do not propose fixes unless
asked.
