# Bad examples: abusing the escape hatch

`allow-long-function` exists for the rare function that really is one
responsibility. These examples were flagged because the marker was used to
skip the analysis, not because the analysis concluded there was one
responsibility.

## Stacking two escape hatches to avoid two separate smells

Bad:

```python
async def switch_to_founding(self, session: AsyncSession, tenant_id: uuid.UUID) -> bool:
    """Move the subscription's sole item back onto the Founding price and clear any scheduled cancellation.

    Returns ``True`` when a Stripe write happened, ``False`` when the subscription was
    already on the Founding price (a repeat submit is then a safe no-op); the resulting
    ``customer.subscription.updated`` webhook is what re-derives ``tier``/``monthly_credit_grant``.
    """
    # allow-long-function: one read-then-write against Stripe, with its own idempotency guard. allow-comment: same.
    self._require_api_key()
    sub = await SubscriptionRepository(session).get_by_tenant(tenant_id)
    if sub is None or not sub.stripe_subscription_id or not is_subscription_active(sub.status):
        raise BadRequestError("this workspace has no active subscription to switch")
    founding_price = _founding_price()
    if sub.current_stripe_price_id == founding_price:
        return False
    if sub.current_stripe_price_id != sub.negotiated_stripe_price_id:
        raise BadRequestError("this workspace is not billing on its negotiated package")
    item_id = await self._sole_subscription_item_id(tenant_id, sub.stripe_subscription_id)
    from_price = sub.current_stripe_price_id or "unknown"
    await self._stripe_write_or_raise(
        tenant_id,
        event="stripe_switch_to_founding_failed",
        message="could not switch this workspace back to the Founding plan",
        call=lambda: self._stripe.v1.subscriptions.update_async(
            sub.stripe_subscription_id,
            params={
                "items": [{"id": item_id, "price": founding_price}],
                "proration_behavior": "create_prorations",
                "cancel_at_period_end": False,
            },
            options={
                "idempotency_key": f"switch-to-founding:{tenant_id}:{sub.stripe_subscription_id}:{from_price}"
            },
        ),
    )
    log.info(
        "stripe_switched_to_founding", tenant_id=str(tenant_id), stripe_subscription_id=sub.stripe_subscription_id
    )
    return True
```

### Why the marker does not hold up

Run the one-sentence test the skill asks for: "Move the subscription's sole
item back onto the Founding price." Now check the body against that
sentence. Four of the seven steps are not that sentence at all — they are
eligibility checks that decide *whether* the move is allowed:

1. `_require_api_key()` — auth precondition.
2. Subscription exists and is active.
3. Already on Founding → no-op.
4. Billing on the negotiated price → otherwise reject.

Only after all four pass does the function do the one thing its name and
docstring claim: resolve the item, call Stripe, log, return `True`. That is
two responsibilities — "can this subscription switch to Founding?" and
"switch it" — glued into one function because the second one is short.

The marker's reason, "one read-then-write against Stripe, with its own
idempotency guard," describes only the second half. It says nothing about
the four guard clauses above it, because the four guard clauses are exactly
the part a real inline-then-split pass would pull out. A reason that
explains the last third of a function is not a reason for the whole
function.

The docstring is a second symptom of the same problem: it already needs two
sentences — what the function does, and a footnote about what the return
value means for a caller who also needs to know about the webhook. A
docstring that cannot stay one sentence is telling you the same thing the
line count is.

Stacking `allow-comment: same` on top compounds it. "Same" is not an
independent reason for the comment smell — it is borrowing the long-function
justification to wave away a second, unrelated finding for free.

### What splitting it actually looks like

```python
async def switch_to_founding(self, session: AsyncSession, tenant_id: uuid.UUID) -> bool:
    """Move the subscription's sole item back onto the Founding price."""
    sub = await self._eligible_for_founding_switch(session, tenant_id)
    if sub is None:
        return False
    return await self._move_to_founding(tenant_id, sub)


async def _eligible_for_founding_switch(self, session: AsyncSession, tenant_id: uuid.UUID) -> Subscription | None:
    """The subscription to switch, or ``None`` when it is already on Founding."""
    self._require_api_key()
    sub = await SubscriptionRepository(session).get_by_tenant(tenant_id)
    if sub is None or not sub.stripe_subscription_id or not is_subscription_active(sub.status):
        raise BadRequestError("this workspace has no active subscription to switch")
    if sub.current_stripe_price_id == _founding_price():
        return None
    if sub.current_stripe_price_id != sub.negotiated_stripe_price_id:
        raise BadRequestError("this workspace is not billing on its negotiated package")
    return sub


async def _move_to_founding(self, tenant_id: uuid.UUID, sub: Subscription) -> bool:
    """Point the subscription's sole item at the Founding price. Always writes."""
    founding_price = _founding_price()
    item_id = await self._sole_subscription_item_id(tenant_id, sub.stripe_subscription_id)
    from_price = sub.current_stripe_price_id or "unknown"
    await self._stripe_write_or_raise(
        tenant_id,
        event="stripe_switch_to_founding_failed",
        message="could not switch this workspace back to the Founding plan",
        call=lambda: self._stripe.v1.subscriptions.update_async(
            sub.stripe_subscription_id,
            params={
                "items": [{"id": item_id, "price": founding_price}],
                "proration_behavior": "create_prorations",
                "cancel_at_period_end": False,
            },
            options={
                "idempotency_key": f"switch-to-founding:{tenant_id}:{sub.stripe_subscription_id}:{from_price}"
            },
        ),
    )
    log.info(
        "stripe_switched_to_founding", tenant_id=str(tenant_id), stripe_subscription_id=sub.stripe_subscription_id
    )
    return True
```

Three one-sentence docstrings instead of one two-sentence one. Each name
passes the one-sentence test on its own. `switch_to_founding` is now the
sentence it claims to be — everything else moved to the method whose name
says what it actually checks.

## Naming the loop's job in a comment instead of in a function

Bad:

```python
async def resolve_tools(
    session: AsyncSession, names: Sequence[str], *, resolver: ToolResolver | None = None
) -> tuple[tuple[RecognizedTool, ...], tuple[str, ...]]:
    """Resolve the classifier's short, already-segmented names into card content.

    allow-long-function: one loop with one job -- resolve each name, dedupe a hit by slug or a
    miss by its sanitized text, then file it into whichever output it belongs in; splitting the
    dedupe from the resolution it depends on would scatter one cohesive pass into pieces that only
    make sense read together.
    """
    resolve = resolver or _resolve_tool_slug
    recognized: list[RecognizedTool] = []
    unrecognized: list[str] = []
    seen_slugs: set[str] = set()
    seen_unrecognized: set[str] = set()
    for name in names:
        wording = name.strip()
        if not wording:
            continue
        match = await resolve(session, _strip_domain_suffix(wording))
        if match is not None:
            slug, _label = match
            if slug not in seen_slugs:
                seen_slugs.add(slug)
                recognized.append(RecognizedTool(slug=slug, label=integration_app_label(slug)))
            continue
        safe_name = _sanitize_echoed_name(wording)
        key = safe_name.casefold()
        if safe_name and key not in seen_unrecognized:
            seen_unrecognized.add(key)
            unrecognized.append(safe_name)
    return tuple(recognized), tuple(unrecognized)
```

### Why the marker does not hold up

The docstring's `allow-long-function` reason already names two distinct
steps — "resolve each name" and "dedupe ... then file it" — and calls them
one job because they run in the same iteration. Running in the same
iteration is not the same as being one responsibility. "Resolve one name
into a recognized tool or leftover text" is a complete sentence on its own,
independent of dedup or of which loop calls it. That sentence is a function
that does not exist yet; the comment describes it instead of the code
containing it.

### What splitting it actually looks like

```python
async def resolve_tools(
    session: AsyncSession, names: Sequence[str], *, resolver: ToolResolver | None = None
) -> tuple[tuple[RecognizedTool, ...], tuple[str, ...]]:
    """Resolve the classifier's short names into recognized tools and leftover text."""
    resolve = resolver or _resolve_tool_slug
    recognized: list[RecognizedTool] = []
    unrecognized: list[str] = []
    seen_slugs: set[str] = set()
    seen_unrecognized: set[str] = set()
    for name in names:
        outcome = await _classify_tool_name(session, name, resolve)
        if isinstance(outcome, RecognizedTool):
            if outcome.slug not in seen_slugs:
                seen_slugs.add(outcome.slug)
                recognized.append(outcome)
        elif outcome:
            key = outcome.casefold()
            if key not in seen_unrecognized:
                seen_unrecognized.add(key)
                unrecognized.append(outcome)
    return tuple(recognized), tuple(unrecognized)


async def _classify_tool_name(
    session: AsyncSession, name: str, resolve: ToolResolver
) -> RecognizedTool | str | None:
    """A recognized tool, sanitized leftover text, or None for a blank name."""
    wording = name.strip()
    if not wording:
        return None
    match = await resolve(session, _strip_domain_suffix(wording))
    if match is not None:
        slug, _label = match
        return RecognizedTool(slug=slug, label=integration_app_label(slug))
    return _sanitize_echoed_name(wording)
```

The loop now visibly does one job — dedupe and file — and the thing it
dedupes and files is produced by a function whose name says what it does.
Neither half needed the escape hatch.

## "One merge pass" hiding a skip check, a key, and a merge

Bad:

```python
def _coalesce_enqueue_effects(
    effects: Sequence[tuple[str, dict[str, Any]]],
) -> list[tuple[str, dict[str, Any]]]:
    # allow-long-function: one merge pass, splitting hides the target lookup | allow-comment: same reason
    """Merge "enqueue" effects sharing a ``coalesce_key``, concatenating their list-valued kwargs.

    Runs on the snapshot ``dispatch_side_effects`` was handed — every savepoint rollback this batch
    will ever take has already happened — so a queuer that opts in gets one dispatch per key without
    the collector ever mutating an already-queued effect, which a rollback could not then undo. ONLY
    list-valued fields merge; every other field keeps the FIRST effect's value, so two same-key
    effects that disagree on a scalar (e.g. ``critical``) silently keep the first's.
    """
    merged: list[tuple[str, dict[str, Any]]] = []
    index_by_key: dict[tuple[Any, Any], int] = {}
    for effect_type, kwargs in effects:
        if effect_type != "enqueue" or "coalesce_key" not in kwargs:
            merged.append((effect_type, kwargs))
            continue
        key = (kwargs.get("task_ref"), kwargs["coalesce_key"])
        payload = {field: value for field, value in kwargs.items() if field != "coalesce_key"}
        if key not in index_by_key:
            index_by_key[key] = len(merged)
            merged.append((effect_type, payload))
            continue
        target = merged[index_by_key[key]][1]
        for field, value in payload.items():
            if isinstance(value, list) and isinstance(target.get(field), list):
                target[field].extend(value)
    return merged
```

### Why the marker does not hold up

"One merge pass" is doing the same trick as the loop example above: it names
the whole `for` block as if the block were the unit, when the block itself
holds three separable questions:

1. Does this effect opt into coalescing at all? (`effect_type`/`coalesce_key` check)
2. What is its dedup key, with the routing field stripped out of the payload?
3. Given an existing target, how do the two payloads combine?

Step 3 is itself a second, nested responsibility — the reason the function
also has a nested `if` inside a nested `for`. None of the three needs the
other two in scope to be written or tested; "combine two payloads, keeping
target's scalars and extending its lists" is a sentence with nothing about
coalesce keys or enqueue effects in it. The reason on the marker, "splitting
hides the target lookup," is the opposite of true — pulling the lookup and
the merge into named functions is what makes each one readable on its own.

The savepoint/rollback paragraph is real and load-bearing, but it is a
constraint on the *caller's contract* (why this runs once per batch, on a
snapshot), not a description of the merge logic. It survives the split
unchanged, attached to the function whose name it explains.

### What splitting it actually looks like

```python
def _coalesce_enqueue_effects(
    effects: Sequence[tuple[str, dict[str, Any]]],
) -> list[tuple[str, dict[str, Any]]]:
    """Merge "enqueue" effects sharing a coalesce_key, concatenating list-valued kwargs.

    Runs on the snapshot ``dispatch_side_effects`` was handed — every savepoint rollback this batch
    will ever take has already happened — so a queuer that opts in gets one dispatch per key without
    the collector ever mutating an already-queued effect, which a rollback could not then undo.
    """
    merged: list[tuple[str, dict[str, Any]]] = []
    index_by_key: dict[tuple[Any, Any], int] = {}
    for effect_type, kwargs in effects:
        key = _coalesce_key(effect_type, kwargs)
        if key is None:
            merged.append((effect_type, kwargs))
            continue
        payload = {field: value for field, value in kwargs.items() if field != "coalesce_key"}
        if key not in index_by_key:
            index_by_key[key] = len(merged)
            merged.append((effect_type, payload))
            continue
        _extend_list_fields(merged[index_by_key[key]][1], payload)
    return merged


def _coalesce_key(effect_type: str, kwargs: dict[str, Any]) -> tuple[Any, Any] | None:
    """This effect's dedup key, or None when it does not opt into coalescing."""
    if effect_type != "enqueue" or "coalesce_key" not in kwargs:
        return None
    return (kwargs.get("task_ref"), kwargs["coalesce_key"])


def _extend_list_fields(target: dict[str, Any], payload: dict[str, Any]) -> None:
    """Extend target's list-valued fields in place with payload's matching lists.

    Every other field keeps target's existing value; two same-key effects that disagree
    on a scalar (e.g. ``critical``) silently keep the first one's.
    """
    for field, value in payload.items():
        if isinstance(value, list) and isinstance(target.get(field), list):
            target[field].extend(value)
```

No more nested `if` inside nested `for`. `_coalesce_key` and
`_extend_list_fields` each pass the one-sentence test standalone; the
scalar-keeping caveat moved to the function it actually describes instead of
sitting in the top docstring next to unrelated rollback context.

## The tell to watch for

Reach for `allow-long-function` and ask whether the reason you are about to
write describes the whole function or only its last few lines. If it only
covers the tail — the actual write, the actual mutation — the head is
probably a separable "is this allowed" responsibility, no matter how short
each individual guard clause looks. Guard clauses that check unrelated
things (auth, existing state, a different resource's state) are not one
responsibility just because each is one line.
