---
name: revenue-analytics
description: Use when a startup wants revenue analytics set up or answered. Walks the user through installing Bruin, choosing and customising a maintained billing template (Stripe, Chargebee, Shopify) to how they actually bill, then answers MRR, ARR, churn, expansion, failed payment and cash collection questions from it.
---

# Revenue analytics

**Status:** experimental · **Risk:** approval-required

> **Upstream documentation wins.** Where this file disagrees with the [Bruin
> docs](https://getbruin.com/docs/bruin/overview.html), `bruin --help`, or your
> billing provider's own documentation, those are right and this file is stale.
> Written against Bruin CLI `v0.11.765`, checked 2026-10-01. The provider's own
> reporting is also the reference you reconcile against, not this file.

Two jobs. **Set up:** work with the user to install a maintained Bruin billing
template and customise it to how this business actually bills. **Answer:**
questions from what it built, in [analysis.md](analysis.md).

The failure mode is not an error message. It is a confident, well formatted,
wrong number that someone forwards to an investor. Most of it is prevented
during setup, by asking the user what the template would otherwise assume.

## Look it up live

This file says what to reach for and what to be careful about. For the facts
themselves, ask the tool, and tell the user if it disagrees with this file:

- **Flags:** `bruin <command> --help`. The docs lag the CLI.
- **Docs:** the local Bruin MCP server, `bruin_get_doc_content('<path>')`, or
  `https://getbruin.com/docs/bruin/<path>.html` without it. For this skill:
  `getting-started/templates-docs/<name>-README` for what a template builds and
  the metric policy it ships, `ingestion/<source>` (for example
  `ingestion/stripe`) for a source's tables and loading modes,
  `ingestion/frankfurter` and `ingestion/exchangeratesapi` for FX rates,
  `core-concepts/semantic-layer` and `quality/overview`.
- **The user's environment:** Bruin Cloud MCP, or
  `bruin cloud ... --output json`.

## Setting it up

Follow [workflow.md](workflow.md) from the top: install, MCP, repository,
warehouse, template, credentials, then the questions. It is the same process
for every skill in this kit. What is specific to revenue is below.

> **Important: do not ask a fixed list of questions.** Read the template as it
> is today and work out which of its choices this user needs to confirm.
> Templates change, so the questions change with them. Workflow step 7 says how.

### Templates to consider

Ask which billing system they use, and whether revenue also arrives elsewhere
(an app store, a second processor, invoices outside the billing system). Then
check `bruin init --help`; at the time of writing the candidates were the
`stripe-*`, `chargebee-*` and `shopify-*` templates, plus `ecommerce`.

Caveats the READMEs will not flag:

- **`stripe-databricks`** is bronze ingestion plus one silver table, with no MRR
  reports, and has no README in the docs. Read the `README.md` it scaffolds.
- **`shopify-bigquery`** only copies raw Shopify tables. The modelling is yours.
- **`ecommerce`** always includes Shopify. It is not a general way to combine
  several billing systems.
- **There is no DuckDB template for Stripe.** If the user wants Stripe without a
  warehouse, that is a project, not a flag. Say so.

For a billing source with no template, read `ingestion/<source>`. Ingesting it
is easy; modelling MRR from it is the work. Agree that with the user before
starting.

### What usually matters here

A lens for reading the template, not a script. For each, find what the template
does, then ask only where this business makes it matter.
[metric-decisions.md](metric-decisions.md) explains each one and what to ask.

- **Billing intervals:** annual or multi-year plans, and how they spread to MRR.
- **Currencies:** more than one, and whether to convert or report per currency.
- **Trials, paused and past-due subscriptions:** which count as MRR.
- **Discounts, taxes, usage billing and one-off charges:** in or out.
- **Timing:** MRR observed at month start, month end, or averaged.
- **Accounts to exclude:** internal, test and free accounts.
- **History:** how far back it matters, and whether the template can backfill
  it. Snapshot-based templates often cannot; the README says.

The Stripe and Chargebee templates already pick defaults for several of these.
Read the metric policy in the README, say what it picked, and confirm each with
the user rather than inheriting it.

### Reconcile against

The billing provider's own dashboard: last month's MRR or active subscription
count is usually the easiest number for the user to check. Expect the
definitions above to explain most gaps, and record each one.

## Answering questions afterwards

Read [analysis.md](analysis.md): what to check before answering, what to state
with every number, and what billing data cannot tell you. If the user is on a
template, read its report assets before writing any SQL. Rebuilding that logic
inline is how two answers to the same question start to differ.

## Never

- **Ask for a credential** in chat or as a command argument. If offered one, say
  not to send it and to rotate it if already sent. Workflow step 6 has the
  safe path.
- **Print a credential**, including in errors, summaries and generated files.
- **Run against production** unless asked by name. Say which environment you used.
- **Pull raw customer records into context** when an aggregate answers the
  question. Use identifiers over names and contact details.
- **Write without asking.** Installing, initialising, editing configuration or
  models, and running a pipeline all wait for the user's yes.

Stop and ask before any write to a source system, outbound message,
publication, credential change, production access, `--full-refresh` or backfill.
On a snapshot-based template, `--full-refresh` after the first load discards MRR
history that cannot be rebuilt from the source. Name that consequence.
