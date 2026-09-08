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

## The tell to watch for

Reach for `allow-long-function` and ask whether the reason you are about to
write describes the whole function or only its last few lines. If it only
covers the tail — the actual write, the actual mutation — the head is
probably a separable "is this allowed" responsibility, no matter how short
each individual guard clause looks. Guard clauses that check unrelated
things (auth, existing state, a different resource's state) are not one
responsibility just because each is one line.
