# Bad examples

Mistakes plans make most often. Each one shows the bad version, why it is bad,
and the fix. The rules behind them live in [SKILL.md](../SKILL.md).

## Solution instead of outcome

> Add an `ExportService` with a `CsvFormatter` strategy.

A solution you have not tested yet, written as the goal. Do not write this in
the plan.

Fix: state what should be true when it is done.

> Users can export their data as CSV.

## Outcomes nobody can perform

- "The tests pass." Which test, and what does it prove.
- "The code compiles." That is not an outcome.
- "`ExportService` is added." That is the solution, not the effect.
- "Export works end to end." Nobody can perform that sentence.

Fix: one action and its result per bullet, in the language of the user.

- Open the orders page.
- Click Export.
- A `.csv` file downloads.

## Steps from an imagined app

- "Open Settings → Billing → Export invoices." The app has no Billing tab under
  Settings, and nothing exports invoices.
- "Log in as an admin and open the admin panel." No admin panel exists.
- "Trigger a payment failure." No user can make a payment fail from the app.

Fix: find each page, button, label, and message in the code before you write
it. For a step no user can cause, name the real command, endpoint request, or
log line.

## Test that needs context

```
1. Backend (integration): A check is queued when the upload lands.

   - Setup: A `.pdf` upload that returns on a platform whose upload lands on return.
   - Input: The upload lands.
   - Expected: A check is queued for that run.
```

What is "a platform whose upload lands on return"? What is "a check", and which
"run"? The words come from a conversation the developer never saw.

Fix: plain words a reader with zero context understands.

```
1. Backend (integration): An uploaded file gets a virus scan.

   - Setup: A user attaches a `.pdf` to a chat message in Slack.
   - Input: The file finishes uploading.
   - Expected: A virus scan job is created for that message.
```

## Test with an "or"

```
1. Backend (integration): An uploaded file gets a virus scan.

   - Setup: A user attaches a `.pdf`, `.pptx`, `.docx` or `.xlsx` to a chat message in Slack.
   - Input: The file finishes uploading.
   - Expected: A virus scan job is created for that message.
```

Four tests hide behind the "or". When it goes red, nobody knows which file type
broke.

Fix: four tests, one per file type: `.pdf`, `.pptx`, `.docx`, `.xlsx`. Write
each one in full.

## Test with too many "and"

```
7. Backend: given the Monthly Client Report folder, when the registry loads,
   then it runs on days 3 to 7 of each month at 08:00, needs any one of Google
   Ads, Meta Ads, LinkedIn Ads, Google Analytics and Google Search Console
   connected by anyone the person can see, is checked before turning on, needs
   no workspace admin, and is not an auto-enrollment candidate.
```

Too many "and" in both the input and the expected result. One sentence checks
six facts. When it goes red, nobody knows which fact broke.

Fix: one test per fact.

```
7. Backend (unit): The Monthly Client Report runs on days 3 to 7 of each month.

   - Setup: The Monthly Client Report folder exists.
   - Input: Load the report registry.
   - Expected: The report schedule covers days 3 to 7 of each month.

8. Backend (unit): The Monthly Client Report runs at 08:00.

   - Setup: The Monthly Client Report folder exists.
   - Input: Load the report registry.
   - Expected: The report run time is 08:00.
```

Then one test each for the required connection, the check before turning on,
the workspace admin, and auto-enrollment.

## Solution that holds code

> Add an `ExportService` with a `CsvFormatter` strategy and a `formatRow()`
> helper.

That is code, and the code has not been read yet. The coding agent picks the
classes, functions, and patterns.

Fix: say what changes, why this way, and what stays untouched.

> CSV export rides on the route that already serves PDF export, because both
> read the same order rows. Only the response format differs.
