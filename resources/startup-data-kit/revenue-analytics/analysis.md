# Answering revenue questions

> **Upstream documentation wins.** Where this file disagrees with the [Bruin
> docs](https://getbruin.com/docs/bruin/overview.html), `bruin --help`, or your
> billing provider's own documentation, those are right and this file is stale.
> Written against Bruin CLI `v0.11.765`, checked 2026-10-01. The provider's own
> reporting is the reference you reconcile against, not this file.

Read this once a revenue pipeline exists and the user is asking questions of
it. If `decisions.md` sits beside the pipeline's `pipeline.yml`, read it first:
it records which conventions this model follows. The `Never` rules in
`SKILL.md` apply here too.

## Before answering any revenue question

1. **Read the model before querying it.** Asset descriptions state the grain,
   the MRR convention and what is excluded. Do not infer meaning from column
   names.
2. **Prefer named metrics over your own SQL.** If a semantic model exists, use
   it. A metric asked for by name returns the same definition every time.
3. **Prefer report tables over raw tables.**
4. **Check freshness first.** A correct number from a stale pipeline is still
   the wrong answer. Read the last runs from Bruin Cloud MCP
   (`pipeline-run-list`, `asset-runs`, or `asset-health` on OXR-orchestrated
   pipelines) or `bruin cloud runs list --output json`, then the maximum date in
   the raw table.

## Always state these alongside a number

- **The definition.** Which metric, which grain, which convention.
- **The window.** The exact months.
- **The source.** Which asset it came from.
- **What is excluded.** Whichever decisions below apply and are unhandled.

Never report MRR without saying how it is observed. Never report a change
without saying what drove it. "MRR fell 3%" is not an answer. "MRR fell 3%
because one Growth account churned and nothing replaced it" is.

## The definitions that change the number

Not edge cases. Each produces a different, defensible MRR, and a model that
picks silently teaches the user that a hard question is settled. The Stripe and
Chargebee templates ship defaults for several of them; read the README's metric
policy and confirm each default with the user rather than inheriting it.

Full detail in [metric-decisions.md](metric-decisions.md). Read it when building
or reviewing a model, not for every question.

The short list: annual and multi-year plans, multiple currencies, usage billing,
trials, paused and past-due subscriptions, discounts, taxes, proration, refunds
and disputes, and whether MRR is observed at month start, month end or averaged.

## Decompose the change, do not just report it

A month-over-month change should break into new, reactivation, expansion,
contraction and churn, and those should sum to the change. Check the
reconciliation before quoting it. If it does not reconcile, say so rather than
picking the number that looks right.

Two traps to check explicitly:

- **Opening balance reported as new business.** Customers acquired before the
  window are not new in month one. This is the most common way a revenue report
  overstates growth.
- **Flat is not nothing happening.** A new customer exactly offsetting a churn
  reads as zero net change. Show the components.

## Separate MRR from cash

They will not match, and the gap is usually the interesting part. MRR is
recurring revenue on a subscription basis. Invoices land on billing
anniversaries and can go unpaid. A customer whose card is failing still carries
MRR.

Report collection rate next to MRR. Falling collections under flat MRR is a
problem that a revenue summary alone hides completely.

## Churn risk from billing alone

Billing signals worth surfacing: unpaid invoices, an invoice written off,
recent contraction, a downgrade.

Each is a question, not a conclusion. A failed invoice is as often an expired
card as a departing customer. Say that. Product usage is what makes churn
prediction real; see the `product-analytics` skill.

## When a number looks wrong

Cheapest first. Usually it is one of the first two.

1. **Check the run.** Every asset succeeded, every quality check passed?
2. **Check freshness.** Maximum date in raw versus the source. A missing recent
   load explains most "revenue dropped" reports.
3. **Reconcile one number by hand.** One month, one customer, from report table
   back to raw record. Report the trace, not just the conclusion.
4. **Check the definition against the question.** Most disagreements about a
   revenue number are disagreements about a definition.
5. **Check what the load can see.** The `stripe-bigquery` raw assets load
   incrementally on Stripe's `created` timestamp, so a subscription cancelled or
   upgraded, or an invoice paid or voided, after its creation window is not
   picked up until a wider re-run. Read the template README's incremental-loading
   section and `ingestion/stripe` before blaming the model.
6. **Check how much history exists.** MRR on the Stripe and Chargebee templates
   comes from daily snapshots. Stripe history starts at the first run and cannot
   be backfilled; Chargebee can backfill subscription episodes but not repricing.
   Movement and retention need two contiguous months of snapshots before they
   classify anything. Empty is not zero.

If the model and the source genuinely disagree, show the gap. Do not adjust a
model to match a number someone expected.

## What billing data cannot tell you

| Asked | Actually needed |
|---|---|
| "Why did they churn?" | A churn reason, a survey, or product usage. Billing data does not contain it. |
| "Which feature drives retention?" | Product analytics on a stable shared identity. See `product-analytics`. |
| "Which channel brings the best customers?" | Ad spend and attribution joined to revenue. See `marketing-analytics`. |
| "What is our LTV?" | A retention curve and a margin assumption. Both are decisions, not queries. |
| "Forecast next quarter" | A stated method and its assumptions. Extrapolating a line is not a forecast. |

Say what is missing and offer the concrete next step. Do not produce an
approximation without labelling it as one.
