---
name: helper-functions-ordering
description: Define every helper function directly below the function that calls it, so a file reads from the whole to the parts. Use when adding a helper, when ordering or moving functions in a file, when a hook reports a helper defined above its caller, or when deciding where a new function goes.
---

# Helper functions ordering

A file is read top to bottom. Put the caller first and its helpers under it.
The reader meets the shape before the detail.

## Not optional

This rule is required. The hook `helper_order.py` blocks on it.

## The shape

Bad — you meet `doA1` with no idea why it exists:

```js
function doA1() {}

function doA2() {}

function doA() {
    doA1();
    doA2();
}

function doB() {}

function doAll() {
    doA();
    doB();
}
```

Good — every function is explained by the one above it:

```js
function doAll() {
    doA();
    doB();
}

function doA() {
    doA1();
    doA2();
}

function doA1() {}

function doA2() {}

function doB() {}
```

## The rule

Depth first. After a function, write everything it calls, in call order, before
you move to its sibling.

`doA1` and `doA2` sit under `doA`, not under `doAll`, because `doA` is what calls
them. A helper belongs to its caller, not to the file.

When two functions call the same helper, put the helper below the first caller.

## Where a new function goes

Directly under the line that calls it. Not at the top of the file, not at the
bottom, not in the alphabetical slot.

The top of the file is for the entry point — the function that names what the
file is for.

## Why this and not the reverse

Bottom-up ordering asks the reader to hold five unexplained helpers in their head
until the payoff arrives. Top-down gives them the summary first, and each step
down is optional detail they can stop reading at.

It also makes an unused helper visible: nothing above it calls it.

## The only exception

A language that requires a definition above its use. C without a prototype,
some Pascal dialects, a shell script calling a function before it is sourced.

Python, JavaScript and TypeScript are not on that list. A `function` declaration
hoists, and a `const` arrow called from inside another function resolves at call
time, not at definition time. Order is free, so order for the reader.

If the module runs the call at import time — a top-level `app = build_app()` —
the definition must come first. That is the language rule again, not a
preference.

## The escape hatch

`allow-helper-order: <reason>` inside the helper. The reason that counts names
the language constraint. "It was already there" is not one — but see
`minimal-scope-plan`: reordering a file you did not otherwise touch is a
separate task.
