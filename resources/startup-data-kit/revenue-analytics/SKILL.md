---
name: revenue-analytics
description: Use when a startup wants revenue analytics set up or answered. Sets up a Stripe, Chargebee or Shopify billing template customised to how they bill and answers MRR, ARR, churn, expansion, failed payment and cash collection questions.
---

# Revenue analytics

**Status:** experimental · **Risk:** approval-required

> **Upstream documentation wins.** Where this file disagrees with the [Bruin
> docs](https://getbruin.com/docs/bruin/overview.html), `bruin --help`, or the
> billing provider's documentation, those are right and this file is stale.
> Written against Bruin CLI `v0.11.766`, checked 2026-10-01.

Sets up a billing template customised to how this business bills and answers
MRR, churn and cash questions. It exists to prevent a confident, well
formatted, wrong MRR that someone forwards to an investor.

## Set up

Follow [workflow.md](workflow.md).

> **Important: do not ask a fixed list of questions.** Read the template as it
> is today and work out which of its choices this user needs to confirm.
> Templates change, so the questions change with them.

**Templates:** `stripe-*`, `chargebee-*`, `shopify-*`, `ecommerce`; confirm
with `bruin init --help`. Ask whether revenue also arrives elsewhere (an app
store, a second processor, invoices outside billing). For a billing source with
no template, read `ingestion/<source>`; the modelling is theirs to build.

**Watch for:**

- `stripe-databricks` is ingestion plus one silver table, and `shopify-bigquery` copies raw tables only: no MRR reports.
- There is no DuckDB template for Stripe; Stripe without a warehouse is a project, not a flag.
- `ecommerce` always includes Shopify; it is not a way to combine billing systems.
- Stripe and Chargebee MRR comes from daily snapshots: Stripe history starts at the first run and cannot be backfilled; Chargebee backfills subscription episodes but not repricing.

> **Note:** `stripe-bigquery` loads incrementally on Stripe's `created`
> timestamp. A cancellation, upgrade, payment or void after the creation window
> is missed until a wider re-run. Check the README's incremental-loading section.

**Usually needs the user's input:**

- Annual and multi-year plans: spread across the term, not booked in the month billed.
- Currencies: fixed rate, rate on the day, or per currency never summed; record the rate and its date.
- Trials, paused and past-due: which count as MRR and customers, after how many days unpaid one stops counting, and whether a lapsed trial is churn.
- Discounts, taxes, proration, refunds: MRR net of discount and pre-tax; proration in cash only or MRR; refunds and disputes in the issue or original month.
- Usage and one-off charges: a separate line, or a labelled smoothing window.
- Timing: MRR observed at month start, month end or daily average; only one in the reports.
- Internal, test and free accounts to exclude.

**Reconcile against:** last month's MRR or active subscription count in the
billing provider's own dashboard.

## Answer questions

Read [analysis.md](analysis.md).

## Never

- Ask for or print a credential; write, run, backfill, `--full-refresh` or
  touch production without a yes; put personal data in output.
- `--full-refresh` a snapshot-based template after its first load without naming that it discards MRR history the source cannot rebuild.
