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

## Solution written as an essay

```
A built-in automation folder may schedule its runs on days of the month instead
of weekdays. The row runs at the folder's time on those days in its own time
zone, which the scheduler already uses, so no day shift is needed. The new
folder carries the report rules in its `AUTOMATION.md` body, because a run
cannot read other files in the folder: only `references/worked-example.md` is
added to every run's instructions, and `references/setup.md` is the guide that
the existing chat setup tool returns. Settings are declared in the folder, so
no Python settings handler is added.

A folder may also ask Patricia to remember which report pages were posted. When
a run of such a folder ends as completed and its final reply reached the chat
with a platform message id, Patricia records the file names of the HTML pages
that the run handed a link for, by saving the page or by asking for its file
link, and that the delivered reply links. A page that an earlier run saved and
this run posted counts too. The newest 200 names are kept on the row next to
the settings. They survive every settings save, are never shown on the
dashboard, and are listed in the next run's instructions under "Pages already
posted", fenced with the tag `automation_posted_pages`. That list lets a run
tell a client already posted apart from a page saved but never posted. It
needs no new chat tool: the native tool list has 109 characters left under its
size limit (measured on `main` at `7e2dedbab0`).
```

Written as an essay, not direct. Long sentences hide each change inside
reasons and side notes. Weak words like "may" leave the developer to guess
whether a thing must happen.

Fix: short, direct bullets, one change each, in one of three shapes.

Copy from an existing pattern:

```
- Copy from the PDF export route in `app/exports/pdf_route.py`.
- Changes for the copy:
  - Serve `text/csv` instead of `application/pdf`.
  - One row per order, header row first: `id,date,customer,total`.
```

Edit existing code:

```
- Edit `app/exports/formats.py`:
  - Before: `FORMATS = ["pdf"]`
  - After: `FORMATS = ["pdf", "csv"]`
```

New code, marked as new:

```
- New: an API endpoint `GET /orders/export.csv` that returns the signed-in
  user's orders as CSV.
- New: a service that turns a list of orders into CSV text.
```
