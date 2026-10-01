---
name: product-analytics
description: Use when a startup wants product analytics set up or answered. Walks the user through installing Bruin, choosing and customising a maintained product template (PostHog, Firebase) to their events, identity and accounts, then answers activation, feature adoption, engagement, retention and usage-based churn questions, including PostHog, Mixpanel or Amplitude usage joined to revenue.
---

# Product analytics

**Status:** experimental · **Risk:** approval-required

> **Upstream documentation wins.** Where this file disagrees with the [Bruin
> docs](https://getbruin.com/docs/bruin/overview.html), `bruin --help`, or
> PostHog, Mixpanel, Amplitude or Firebase documentation, those are right and
> this file is stale. Written against Bruin CLI `v0.11.765`, checked 2026-10-01.
> The product analytics tool's own UI is also the reference you reconcile
> against, not this file.

Two jobs. **Set up:** work with the user to install a maintained Bruin product
analytics template and customise it to their events, users and accounts.
**Answer:** questions from what it built, in [analysis.md](analysis.md).

Event data is the one source that can explain *why* revenue moved. It is also
the one where the data you need most often turns out never to have been
captured. The failure mode is a confident adoption or retention number built on
the wrong identity, the template's example events, or an activation nobody
defined. Most of it is prevented during setup, by asking the user what the
template would otherwise assume.

## Look it up live

This file says what to reach for and what to be careful about. For the facts
themselves, ask the tool, and tell the user if it disagrees with this file:

- **Flags:** `bruin <command> --help`. The docs lag the CLI.
- **Docs:** the local Bruin MCP server, `bruin_get_doc_content('<path>')`, or
  `https://getbruin.com/docs/bruin/<path>.html` without it. For this skill:
  `getting-started/templates-docs/<name>-README` for what a template builds and
  needs, `ingestion/<source>` (for example `ingestion/posthog` or
  `ingestion/mixpanel`) for a source's tables and connection fields, and
  `commands/init` for `--merge`.
- **The user's environment:** Bruin Cloud MCP, or
  `bruin cloud ... --output json`.

## Setting it up

Follow [workflow.md](workflow.md) from the top: install, MCP, repository,
warehouse, template, credentials, then the questions. It is the same process
for every skill in this kit. What is specific to product analytics is below.

> **Important: do not ask a fixed list of questions.** Read the template as it
> is today and work out which of its choices this user needs to confirm.
> Templates change, so the questions change with them. Workflow step 7 says how.

### Templates to consider

Ask which product analytics tool they use, and whether billing data already sits
in the warehouse, because the join to revenue is where most of the value is.
Then check `bruin init --help`; at the time of writing the candidates were
`posthog-bigquery` and `firebase`, plus Mixpanel as an option inside
`ecommerce`.

Caveats that change what the user can report:

- **`posthog-bigquery`: backfill `posthog_raw.events` one day per run.** A wider
  window silently returns partial data. Plan the first-run window (workflow
  step 9) around this. The README has the loop, and notes the end date is the
  next day.
- **`posthog-bigquery`: the account layer needs person properties** set by
  `identify`. Without `company`, `accounts` and the account-grain reports are
  empty; without `signup_date`, retention cohorts are empty; without `plan`,
  every account reads `unknown`. `persons` is current state, so today's plan is
  carried onto past months. Identity resolves through
  `posthog_stage.person_distinct_ids`, accounts through `posthog_stage.accounts`.
- **`posthog-bigquery`: the event lists are examples.** The `pipeline.yml`
  variables ship the template author's own event names. None of them will match
  this product until replaced.
- **`posthog-bigquery`: `bruin validate` reports `in_string_list is not
  callable`** on assets that call its macros. The README says this is harmless.
  Do not "fix" it.
- **`firebase`** models a Firebase Analytics export that is already in BigQuery.
  There is no Firebase ingestion connector, so the export has to be switched on
  first. Read the `README.md` it scaffolds as well as the docs page: the
  scaffolded one has the setup steps (rename `analytics_123456789` to their
  analytics ID, choose the intraday or daily export, work through the `TODO`
  comments).
- **`ecommerce`** offers Mixpanel as its web analytics option, but always
  includes Shopify. It is not a product analytics template.
- **Mixpanel, Amplitude, RevenueCat, Adapty** have connectors and no template.
  Read `ingestion/<source>`. Ingesting is easy; modelling activation and
  retention from it is the work. Agree that with the user before starting.

**Adding PostHog to an existing billing pipeline** uses
`bruin init posthog-bigquery <existing-pipeline-folder> --merge`. It copies
assets and macros, never overwrites, and leaves `pipeline.yml` alone. The
PostHog raw assets take their `source_connection` from the template's ingestr
`default:` block, and its `variables` are missing too. Merged into a pipeline
with its own `default:` block, such as `stripe-bigquery`, the PostHog raw assets
inherit the wrong connection. Copy what they need across, set the connection on
those assets, or keep PostHog as its own pipeline. Show the diff to
`pipeline.yml` before applying it.

### What usually matters here

A lens for reading the template, not a script. For each, find what the template
does, then ask only where this business makes it matter.
[analysis.md](analysis.md) explains the identity and activation points in depth.

- **Identity:** which ID ties a product user to a billing customer, and whether
  it exists on both sides. Agree it before anything is built on it, then check
  the match rate. `posthog-bigquery` exposes `company` and `email` on
  `posthog_stage.persons`; the `firebase` template keys users on `user_id`, with
  a `TODO` to switch to `user_pseudo_id`. If no stable key exists, the fix is in
  the product, not the pipeline. Say so.
- **Account or user grain:** B2B accounts with seats, or individual users. On
  `posthog-bigquery`, ask whether seat activation should count against known
  users or contracted seats (`seat_denominator`).
- **Activation and "active user":** which event, in which window. Ask for the
  definition; if there is none, propose one, label it provisional, and record it
  in `decisions.md`. `posthog-bigquery` has no activation setting; the nearest
  choices are its `product_action_events` and `conversion_events` lists.
- **Which events matter:** the product's own event names, and when each was
  instrumented or renamed. An instrumentation date reads as an adoption trend.
- **Person and plan properties:** whether the product sends the ones the
  template reads, under which names. If billing is already in the warehouse,
  ask whether plan and MRR should come from there instead of person properties.
- **Users to exclude:** employees, test accounts, staging projects, anonymous
  visitors. Check whether the template filters any of them.
- **History:** how far back it matters. The tool's own retention window bounds
  what exists, and PostHog history loads one day per run.

### Reconcile against

The product analytics tool's own UI: one event's count for one fully loaded
recent day, or weekly active users over a recent window if both define "active"
the same way. Compare the raw table first, then the staged one. Expect
deduplication, identity merges and excluded users to explain most gaps, and
record each one.

## Answering questions afterwards

Read [analysis.md](analysis.md): what to check before answering, the identity
join and instrumentation gaps, activation, retention curves, and why
correlation is not cause. If the user is on a template, read its report assets
before writing any SQL. Rebuilding that logic inline is how two answers to the
same question start to differ.

## Never

- **Ask for a credential** in chat or as a command argument. If offered one, say
  not to send it and to rotate it if already sent. Workflow step 6 has the
  safe path.
- **Print a credential**, including in errors, summaries and generated files.
- **Run against production** unless asked by name. Say which environment you used.
- **Send an event or write to the product analytics tool.** Read only.
- **Pull raw user-level event streams into context.** They are enormous and
  usually contain personal data. Aggregate first, in SQL, then look.
- **Include personal data in output.** Event payloads carry emails, names, IPs,
  URLs with tokens, and sometimes more. Mask or aggregate before it reaches a
  summary. Use identifiers over names and contact details.
- **Treat an event property as trustworthy** because it exists. Check the fill
  rate before segmenting on it.
- **Write without asking.** Installing, initialising, editing configuration or
  models, and running a pipeline all wait for the user's yes.

Stop and ask before any write to a source system, outbound message,
publication, credential change, production access, `--full-refresh` or backfill.
On `posthog-bigquery`, `--full-refresh` truncates `posthog_raw.events` and
reloads only the run's window, so every earlier day has to be backfilled again,
one day per run. Name that consequence.
