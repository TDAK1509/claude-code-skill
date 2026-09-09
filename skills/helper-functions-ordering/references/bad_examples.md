# Bad examples

## A file that passes the hook and still reads backwards

A 456-line Python script that re-chains an Alembic migration fork. Entry point
`main`, then `resolve`, then forty-one helpers.

`helper_order.py` reports **no violations** on it. Not one helper is defined
above its caller. The file still reads backwards.

The hook checks one half of the rule: no helper above its caller. The other half
is call order, and no hook checks it. That half is yours.

### The defect

```python
def resolve(*, repo: Path, base_ref: str, hygiene_path: Path) -> int:
    head_candidates, base_candidates, early_exit = _load_trees(repo, base_ref)
    if early_exit is not None:
        return early_exit
    classified = _classify_fork(head_candidates, base_candidates, base_ref)
    if isinstance(classified, int):
        return classified
    target, base_head_id, chain = classified
    reason = _first_refusal(hygiene_path, base_candidates, head_candidates, target, chain)
    if reason is not None:
        return _refuse(reason)
    return _apply_fix(repo, target, base_head_id)


def _refuse(reason: str) -> int:
    ...


def _apply_fix(repo: Path, target: Candidate, base_head_id: str) -> int:
    ...


def _load_trees(repo: Path, base_ref: str) -> tuple[...]:
    ...
```

`resolve` calls five helpers in this order:

1. `_load_trees`
2. `_classify_fork`
3. `_first_refusal`
4. `_refuse`
5. `_apply_fix`

The file defines them in the order 4, 5, 1, 2, 3.

The reader arrives at `resolve`, reads its first line, and goes looking for
`_load_trees`. It is not there. Two exit paths are there instead. The function
directly below a caller must be the one that caller uses first.

### Four defects, all the same defect

| Function | Defined at | Belongs at | Why |
| --- | --- | --- | --- |
| `_refuse` | 3 | 15 | `resolve`'s 4th call, placed as if it were the 1st |
| `_apply_fix` | 4 | 36 | `resolve`'s last call, placed 2nd |
| `_other_head` | 18 | 29 | `_classify_fork`'s last call, placed as its first helper |
| `_missing_parents` | 25 | 24 | `_link_parent` calls `_normalize_parents` first |

### Depth first, not breadth first

```
_load_candidates
_safe_tree_entries              <- child 1
_load_candidates_from_entries   <- child 2, jumped the queue
_tree_entries                   <- child 1's subtree, arrives late
_run_git
_git
_load_versions_entry            <- child 2's subtree
```

`_load_candidates` calls `_safe_tree_entries`, then
`_load_candidates_from_entries`. The file writes both children, then both
subtrees. That is breadth first.

Depth first finishes a child completely before it starts the next one:

```
_load_candidates
_safe_tree_entries
_tree_entries
_run_git
_git
_load_candidates_from_entries
_load_versions_entry
```

The reader can stop at any depth. Breadth first gives them no place to stop.

### The shared helpers

Four helpers have more than one caller:

- `_refuse` — six callers, the first is `resolve`
- `_normalize_parents` — five callers, the first is `_link_parent`
- `_run_git` — two callers, the first is `_tree_entries`
- `_graph_defects` — two callers, the first is `_two_heads`

Each one goes below its **first** caller, at that caller's call position. It does
not move to the bottom of the file, and it does not move to the top because six
functions need it. Six callers is not a reason to promote a helper; it is a
helper that six functions happen to share.

### What the fix is

Cut and paste. Forty-four function bodies, none of them edited. Reordering
changes no behaviour in Python, because a module-level `def` binds at import
time and the calls run later. Commit the move on its own.
