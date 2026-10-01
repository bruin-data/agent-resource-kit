---
name: product-analytics
description: Use when a startup wants product analytics set up or answered. Sets up a PostHog or Firebase template customised to their events, identity and accounts and answers activation, adoption, retention and usage-based churn questions, including usage joined to revenue.
---

# Product analytics

**Status:** experimental · **Risk:** approval-required

> **Upstream documentation wins.** Where this file disagrees with the [Bruin
> docs](https://getbruin.com/docs/bruin/overview.html), `bruin --help`, or
> PostHog, Mixpanel, Amplitude or Firebase documentation, those are right and
> this file is stale. Written against Bruin CLI `v0.11.766`, checked 2026-10-01.

Sets up PostHog or Firebase product analytics and answers activation, adoption
and retention questions, joined to revenue. It exists to prevent a confident
adoption or retention number built on the wrong identity, the template's
example events, or an activation nobody defined.

## Set up

Follow [workflow.md](workflow.md).

> **Important: do not ask a fixed list of questions.** Read the template as it
> is today and work out which of its choices this user needs to confirm.
> Templates change, so the questions change with them.

**Templates:** `posthog-bigquery`, `firebase`; confirm with `bruin init --help`.
`ecommerce` offers Mixpanel but always includes Shopify. Mixpanel, Amplitude,
RevenueCat and Adapty have connectors and no template: read
`ingestion/<source>`; the modelling is theirs to build.

**Watch for:**

- `posthog-bigquery`'s event lists in `pipeline.yml` are the template author's examples; none match this product until replaced.
- `posthog-bigquery` account reports and retention cohorts are empty unless the product sets person properties with `identify`; those are current state, so today's plan is carried onto past months.
- `firebase` models a Firebase Analytics export already in BigQuery; there is no Firebase connector, so the export must be switched on first.

> **Note:** backfill `posthog-bigquery` events one day per run. A wider window
> silently returns partial data. The README has the loop.

**Usually needs the user's input:**

- Identity: which ID ties a product user to a billing customer, and whether it exists on both sides; if none, the fix is in the product.
- Grain: B2B accounts with seats or individual users; seat activation against known users or contracted seats.
- Activation and "active user": which event in which window; if none, propose one labelled provisional.
- Which events matter, and when each was instrumented or renamed.
- Person and plan properties: whether the product sends them, under which names, or whether plan comes from billing.
- Users to exclude: employees, test accounts, staging projects, anonymous visitors.
- History: how far back matters; the tool's own retention bounds what exists.

**Reconcile against:** one event's count for one fully loaded recent day in the
product analytics tool's own UI, raw table first, then staged.

## Answer questions

Read [analysis.md](analysis.md).

## Never

- Ask for or print a credential; write, run, backfill, `--full-refresh` or
  touch production without a yes; put personal data in output.
- Send an event or write to the product analytics tool.
- Pull raw user-level event streams into context; aggregate in SQL first.
