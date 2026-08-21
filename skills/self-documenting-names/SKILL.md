---
name: self-documenting-names
description: Write code that explains itself through names instead of comments. Use when adding or reviewing comments, when a comment explains what code does, when naming variables, functions, classes or files, when a hook reports a comment or an over-long name, or when the user asks to clean up comments or improve naming.
---

# Self-documenting names

Never comment on code. A comment that explains code is evidence that the code
does not explain itself. Rename until the code says what the comment said, then
delete the comment.

## The rule

1. You want to write a comment. Stop.
2. Read the comment. It describes what the code does or why it exists.
3. Move that meaning into a name: the variable, the function, the class, or a new
   extracted function whose name is the sentence you were about to write.
4. Delete the comment.

## Naming

Long names beat comments. Do not fear a long name.

- `retryCountAfterRateLimit` beats `n` plus a comment.
- `isEligibleForVipDiscount` beats `flag` plus a comment.

But long is not unlimited. **Ten words is the maximum.** Count words in
`snake_case`, `camelCase` and `PascalCase` alike. A name that needs eleven words
is not a naming problem; it is a function doing two things. Split it — see the
`oversized-function` skill.

The only exception: Python test functions. `test_user_cannot_delete_another_users_draft_order`
is a specification, not a name. Let those run long.

## Docstrings

Only when a repository rule requires them. Then keep them minimal: **one or two
sentences.** No parameter tables, no restating the signature, no usage essays.

When you add to a docstring that is already long, add one or two sentences at
most. Do not extend the existing style.

## What is not a comment on code

These stay, because they do not explain what code does:

- Directives the tools need: `# type:`, `# noqa`, `// @ts-expect-error`, `// eslint-disable-next-line`.
- Licence and copyright headers.
- `TODO` and `FIXME` markers that record work, not meaning.

## When a comment survives

Rarely, meaning cannot live in a name: a non-obvious external constraint, a
workaround for a third-party bug, a link to a specification. Write it as *why*,
never as *what*, and keep it to one line.

## Applying this

- Before writing any comment, try three names first.
- When you delete a comment, say which name absorbed it.
- Never leave commented-out code. Delete it; the history keeps it.
