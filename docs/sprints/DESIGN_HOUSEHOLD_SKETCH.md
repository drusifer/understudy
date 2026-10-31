# Household as a sketch (draft for the owner, 2026-10-30)

Draft only; nothing here is built. Per decision 36 the old ETL structure is not kept. Its frozen result
(`tests/fixtures/etl/household/`) says what the sketch must mean. Names marked **NEW** do not exist yet and need the
owner's word before code.

```yaml
name: household
sources:
  monarch: { file: "{{ monarch }}", format: csv }   # NEW: format csv (decision 17 cut it; needed now)
  amex:    { file: "{{ amex }}",    format: csv }
  merged:                                           # a purchase seen in both files is one record
    kind: stage
    do: { map: { action: pair } }                   # NEW general map: match two sources one-to-one on date and amount
    with: { source: monarch, other: amex, on: [date, amount], flip: true }
  legs:                                             # card payments: a debit and a credit on the same day
    kind: stage
    do: { map: { action: pair } }
    with: { source: merged, other: merged, on: [date, amount], flip: true, where: { category: { eq: Transfer } } }
  payees:                                           # unpaired transfer candidates, one row per payee
    kind: stage
    do: { map: { action: group } }                  # NEW general map: group rows, count them, keep examples
    with: { source: legs, by: payee }
  refunds:
    kind: stage
    do: { map: { action: pair } }                   # a refund and the earlier charge(s) it could reverse
    with: { source: merged, other: merged, on: [merchant], where: { amount: { gt: 0 } } }
  merchants:
    kind: stage
    do: { map: { action: group } }
    with: { source: merged, by: merchant }

machine:
  initial: payees_judged
  states:
    payees_judged:                                  # Jev, once per payee
      do: { sketch: { file: judge_payee } }
      each: payees
      then: refunds_linked
    refunds_linked:                                 # Jev, only where a refund has several candidate originals
      do: { sketch: { file: link_refund } }
      each: refunds
      then: merchants_placed
    merchants_placed:                               # Jev, once per merchant
      do: { sketch: { file: place_merchant } }
      each: merchants
      then: write
    write:
      do: { sink: { name: records } }
      then: done
    done: { final: true, outcome: written }
sinks:
  records: result.jsonl
```

Each child is the evening's `review_score` shape: a Jev source (`criteria` = the levels, `state` = rows about one
payee, refund or merchant) and one stage that turns Jev's probabilities into a row.

## What this leaves open (owner's call)

1. **CSV:** bring back `format: csv`? (Decision 17 cut it.)
2. **Does `pair` cover pairing, transfer legs and refunds,** or are they three different things? Refunds pick among
   several candidates (Jev); purchases and legs pair one-to-one.
3. **Where the final record is assembled** (kind, category, status per transaction): a `map.join` chain over the
   sources above, or one `assemble` map.
4. **What happens to SQL:** none of this needs a database. The old SQLMesh models would be dropped, not wrapped.
5. **Thresholds** (a payee above 0.7 is an external transfer, below 0.3 spending, between them review): a
   `map.where` pair, or a `classify` map.
