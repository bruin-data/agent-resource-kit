# Answering revenue questions

> **Upstream documentation wins.** Where this file disagrees with the [Bruin
> docs](https://getbruin.com/docs/bruin/overview.html), `bruin --help`, or the
> billing provider's documentation, those are right and this file is stale.
> Written against Bruin CLI `v0.11.766`, checked 2026-10-01.

Read `decisions.md` beside the pipeline's `pipeline.yml` first. The Never rules
in [SKILL.md](SKILL.md) apply.

## Before answering

- Read the report assets, and the semantic model if one exists, before writing SQL; ask for metrics by name.
- Check freshness: the last runs (Bruin Cloud MCP or `bruin cloud runs list`), then the maximum date in the raw table.
- State the definition, MRR timing convention, window, source asset and any unhandled exclusion with every number.
- Break a change into new, reactivation, expansion, contraction and churn, check they sum, and say so if they do not.

## Traps

- Invoices and cash are not MRR: a customer with a failing card still carries MRR; report collection rate beside it.
- An annual plan booked in the month it was billed is the largest source of overstated MRR.
- Customers acquired before the window are not new business in month one.
- Flat net MRR can hide a new customer offsetting a churn; show the components.
- On snapshot-based templates, movement and retention need two contiguous months of snapshots; empty is not zero.
- A failed or written-off invoice is a question, not churn; it is as often an expired card.

## What this data cannot tell you

- Why a customer churned: that needs a churn reason, a survey or product usage (`product-analytics`).
- Which channel brings the best customers: that needs spend and attribution (`marketing-analytics`).
- LTV: it needs a retention curve and a margin assumption, both decisions.
- A forecast: it needs a stated method and assumptions, not an extrapolated line.
