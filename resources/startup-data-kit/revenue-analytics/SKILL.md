---
name: revenue-analytics
description: Use when answering questions about MRR, ARR, churn, retention, expansion, contraction, failed payments, cash collection or revenue changes from billing data such as Stripe, Chargebee, Paddle or RevenueCat, or when building and reviewing revenue models and metric definitions.
---

# Revenue analytics

**Status:** experimental · **Risk:** read-only

> **Upstream documentation wins.** Where this file disagrees with the [Bruin
> docs](https://getbruin.com/docs/bruin/overview.html), `bruin --help`, or your
> billing provider's own documentation, those are right and this file is stale.
> Written against Bruin CLI `v0.11.765`, checked 2026-09-29. The provider's own
> reporting is also the reference you reconcile against, not this file.

The failure mode here is not an error message. It is a confident, well formatted,
wrong number that someone forwards to an investor. Everything below exists to
make that less likely.

Setup is in the `bruin-agent` skill. This assumes a project exists.

## Sources and where to start

| They use | Start with |
|---|---|
| Stripe, BigQuery | `bruin init stripe-bigquery` |
| Stripe, Databricks | `bruin init stripe-databricks` |
| Chargebee | `bruin init chargebee-bigquery` |
| Shopify | `shopify-duckdb`, `shopify-bigquery` or `shopify-clickhouse` |
| Several sources at once | `ecommerce` |
| Paddle, Recurly, RevenueCat, Adapty, Square, FastSpring, Solidgate, Primer, Wise | Connector exists, no template. Ingest with an `ingestr` asset and model it yourself. |

`stripe-bigquery` already publishes MRR by customer, MRR movements, subscription
KPIs and invoice billings. Read those assets before writing any SQL. Rebuilding
that logic inline is how two answers to the same question start to differ.

Multi-currency: `frankfurter` needs no credentials, `exchangeratesapi` needs a
key. Decide the conversion policy before wiring either in.

## Before answering any revenue question

1. **Read the model before querying it.** Asset descriptions state the grain,
   the MRR convention and what is excluded. Do not infer meaning from column
   names.
2. **Prefer named metrics over your own SQL.** If a semantic model exists, use
   it. A metric asked for by name returns the same definition every time.
3. **Prefer report tables over raw tables.**
4. **Check freshness first.** A correct number from a stale pipeline is still
   the wrong answer.

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
picks silently teaches the user that a hard question is settled.

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

If the model and the source genuinely disagree, show the gap. Do not adjust a
model to match a number someone expected.

## Never

- **Ask for a credential** in chat or as a command argument. If offered one, say
  not to send it and to rotate it if already sent.
- **Print a credential**, including in errors, summaries and generated files.
- **Run against production** unless asked by name. Say which environment you used.
- **Pull raw customer records into context** when an aggregate answers the
  question. Use identifiers over names and contact details.

Stop and ask before any write to a source system, outbound message,
publication, credential change, production access, `--full-refresh` or backfill.

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

## Reference

- Stripe template: https://getbruin.com/docs/bruin/getting-started/templates-docs/stripe-bigquery-README.html
- Semantic layer: https://getbruin.com/docs/bruin/core-concepts/semantic-layer.html
- Quality checks: https://getbruin.com/docs/bruin/quality/overview.html
