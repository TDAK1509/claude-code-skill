---
name: minimal-scope-plan
description: Plan a task as the smallest change that reaches the goal, and decide when touching an out-of-scope file is justified. Use when planning or scoping work, when writing an implementation plan, when a fix seems to need edits across many files, when tempted to refactor or clean up code the task did not ask about, or when the user asks how large a change should be.
---

# Minimal scope plan

Reach the goal with as little work as possible. Every file you open that the
goal did not name is a cost: more review, more risk, more to revert.

## Not optional

This rule is required. It is not a style preference.

No hook enforces it, so nothing will stop you from skipping it. That makes it
easier to drop under time pressure, not less binding.

## Start from the goal

Write the goal in one sentence before you plan. Then list the smallest set of
files that can satisfy that sentence. That list is the scope.

If you cannot write the goal in one sentence, you have more than one task. Split
them and plan the first.

## The default is: do not touch it

A file outside the scope stays untouched. This holds even when the file is ugly,
even when the fix is obvious, even when you are already reading it.

Bad code you did not cause is not this task.

## The three reasons to widen the scope

Touch an out-of-scope file only when one of these is true.

1. **Your change alters how that file behaves.** A caller, a subclass, a test, a
   type, a schema consumer. If leaving it alone changes a feature the user did
   not ask to change, it is in scope. Silent behaviour change is the failure to
   avoid.
2. **Your solution opens a security hole.** A new input path, a widened
   permission, a leaked secret, a bypassed check. Fix it inside this task.
3. **Your solution creates a performance leak.** An unbounded query, a loop over
   a network call, an unreleased handle, a cache that never evicts. Fix it inside
   this task.

Nothing else qualifies. Not style, not naming in untouched code, not a refactor
you would enjoy, not an unrelated bug.

## When you find something else

You will find unrelated problems. Report them; do not fix them.

State the file, the problem, and the risk in one line each. The user decides
whether it becomes the next task.

## Before you write the plan

Ask, for each step:

- Does this step move the goal sentence forward? If not, delete it.
- Does a smaller version of this step work? Prefer it.
- What breaks if I skip this step? If nothing, skip it.

## Applying this

- Name the in-scope files in the plan. Name any out-of-scope file separately,
  with which of the three reasons put it there.
- Prefer changing one function to changing one file. Prefer changing one file to
  changing one module.
- A large diff needs a reason, not an apology.
