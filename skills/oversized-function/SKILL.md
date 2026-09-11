---
name: oversized-function
description: Refactor a function that is too long by finding its real responsibility boundaries instead of extracting helpers to hit a line count. Use when a function is over ~12 lines, when a linter or reviewer flags "function too long" / "too many lines" / "oversized function", or when the user asks to split, shorten, or clean up a long function or method.
---

# Oversized function

Functions over 12 lines tend to bundle multiple responsibilities.
Functions over 12 lines almost always carry more than one responsibility, and that
is the smell to chase — not the line count itself.

## Not optional

This rule is required. It is not a style preference and not a default you may
weigh against convenience.

When the hook blocks you, load this skill and do what it asks. Then decide.
Reaching for `allow-long-function` before you have tried the rename is not a
judgement call; it is a skipped step. The escape hatch needs a written reason,
and "it matches the file's existing style" is not one. House style is how the
file got this way.

## Analyse responsibilities first

Ask what distinct concerns this function handles. Then ask:

1. Are these separate responsibilities that belong in different methods?
2. Should this become a class with multiple methods?
3. Can you group cohesive data into objects to reduce local variables?

## Avoid mechanical extraction

Pulling out a `helperA` / `helperB` purely to satisfy the threshold often hides the
smell behind worse names and leaves the real shape untouched. Find true
responsibility boundaries.

## A loop body is a function without a name

A `for` loop that resolves, then dedupes, then files an item into one of
several outputs is doing more than one thing per iteration. The resolve step
is a separable responsibility even though it runs once per item — give it a
name and extract it, the same as any other responsibility. A docstring or
comment that names what the loop does is a sign a function should have that
name instead. See `references/bad_examples.md` for a worked case.

## Inline before you split

If responsibilities are tangled you may need to first inline methods to see the
whole picture before redistributing. Think of this when reducing line count seems
particularly hard — stepping backwards often opens up better possibilities.

## The one-sentence test

A concrete technique: write what the method does in one short sentence. Refactor
until the code reads as close to that sentence as possible. If you cannot say what
a method does in one sentence, it almost certainly has more than one
responsibility.

## The escape hatch is not a description of the tail

A reason on `allow-long-function` must justify the whole function, not just
its last few lines. If the function is guard clauses followed by one real
action, the reason usually only describes the action — that is the sign the
guard clauses are a separable "is this allowed" responsibility, even when
each clause is one line. See
`references/bad_examples.md` for a worked case of this: a Stripe write
wrapped in four unrelated eligibility checks, marked `allow-long-function`
with a reason that covers only the write.

## Generated files are out of scope

Do not apply this rule to generated code: `openapi.json`, generated API clients
and type definitions, `*.gen.ts`, `*.d.ts`, protobuf output, migrations, and any
file whose header says it was generated.

Never hand-edit that output. Change the schema, the template or the generator,
then regenerate. The hooks skip these paths for the same reason.

## Applying this

- Name each responsibility out loud before you move any code.
- Propose the target shape (methods, class, value objects) before editing.
- Keep behaviour identical; run the existing tests after the refactor.
- Report the one-sentence description of every method you end up with.
