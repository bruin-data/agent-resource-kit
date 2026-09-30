---
name: product-analytics
description: Use when analysing product usage, activation, feature adoption, engagement, retention curves or user behaviour from PostHog, Mixpanel, Amplitude or Firebase, and when joining product usage to revenue to explain or predict churn.
---

# Product analytics

**Status:** experimental · **Risk:** read-only

> **Upstream documentation wins.** Where this file disagrees with the [Bruin
> docs](https://getbruin.com/docs/bruin/overview.html) or with PostHog,
> Mixpanel, Amplitude or Firebase documentation, those are right and this file
> is stale. Written against Bruin CLI `v0.11.765`, checked 2026-09-30.

Event data is the one source that can explain *why* revenue moved. It is also
the one where the data you need most often turns out never to have been
captured.

Setup is in the `bruin-agent` skill. This assumes a project exists.

## Look it up live

This file says what to reach for and what to be careful about. For the facts
themselves, ask the tool, and tell the user if it disagrees with this file:

- **Flags:** `bruin <command> --help`. The docs lag the CLI.
- **Docs:** the local Bruin MCP server, `bruin_get_doc_content('<path>')`, or
  `https://getbruin.com/docs/bruin/<path>.html` without it. For this skill:
  `getting-started/templates-docs/posthog-bigquery-README` and
  `getting-started/templates-docs/firebase-README` for what each template builds
  and needs, `ingestion/<source>` (for example `ingestion/mixpanel`) for a
  source's tables and connection fields, and `commands/init` for `--merge`.
- **The user's environment:** Bruin Cloud MCP, or
  `bruin cloud ... --output json`.

**Credentials.** Never ask for one in chat or pass one as a command argument.
For a source, the user runs `bruin connections add` with no flags (the
interactive prompt; its flag mode puts the secret on the command line) or
references `${VAR}` in `.bruin.yml`. For Cloud, `bruin cloud login` or an
exported `BRUIN_CLOUD_API_KEY`, never `--api-key`. `bruin auth status` shows
which is active without printing it.

## Sources and where to start

Run `bruin init --help` for the current template list, then read the README of
the one you pick.

- **PostHog on BigQuery: `posthog-bigquery`.** Two things in its README change
  what you can report. Backfill `posthog_raw.events` one day per run: a wider
  window silently returns partial data. And the account layer is built from
  person properties set by `identify`: without `company`, `accounts` and the
  account-grain reports are empty; without `signup_date`, retention cohorts are
  empty; without `plan`, every account reads `unknown`. `persons` is current
  state, so today's plan is carried onto past months. Identity resolves through
  `posthog_stage.person_distinct_ids`, accounts through `posthog_stage.accounts`.
- **Firebase: `firebase`.** It models a Firebase Analytics export that is
  already in BigQuery. There is no Firebase ingestion connector, so the export
  has to be switched on first.
- **Mixpanel, Amplitude, RevenueCat, Adapty, feedback and NPS tools.**
  Connectors without a template. Read `ingestion/<source>`, ingest, and model it
  yourself.

Adding PostHog to an existing billing pipeline:

```bash
bruin init posthog-bigquery <existing-pipeline-folder> --merge
```

The folder must already contain `pipeline.yml`. `--merge` copies assets and
macros and never overwrites, but it does not merge `pipeline.yml`. The PostHog
assets need the template's `variables` and its ingestr `default:` block. Merged
into a pipeline that already has its own `default:` block, such as
`stripe-bigquery`, the PostHog raw assets inherit the wrong
`source_connection`. Copy what they need across, set the connection on those
assets, or keep PostHog as its own pipeline. Show the user the diff to
`pipeline.yml` before applying it.

## Establish the identity join first

This is the whole job, and doing it second means redoing everything built on top.

Product events identify a **user**. Billing identifies an **account**. They are
different grains, and the mapping between them is your problem:

- One account has many users. Usage is per account, seats are per user, and the
  two questions have different answers.
- Anonymous events before signup may or may not be stitched to the person after.
- A person may appear under several identifiers across devices.
- Self-serve and sales-led signups often carry different identifiers entirely.

**Before joining usage to revenue, verify the key exists and check the match
rate.** Report it: "82% of paying accounts matched to product usage" is a useful
caveat. Silently analysing the 82% and calling it the customer base is not.

If no stable key exists, say that the join is the work. It usually means a
change in the product, not in the pipeline.

## Event data does not tell you what was never instrumented

The most important sentence in this skill.

An event that was never captured and an event that never happened look
identical downstream. Before concluding a feature is unused, check whether it
was ever instrumented, and when instrumentation was added.

- **Instrumentation dates create fake trends.** Adoption that starts at zero in
  March often means the event shipped in March.
- **Renamed events break history.** A rename looks like one feature dying and
  another being born.
- **Missing properties cannot be recovered retroactively.** If plan tier was
  never on the event, you cannot segment history by it.
- **Client-side events are lost** to ad blockers, offline use and crashes.
  Server-side events are more complete and usually fewer.

Always say which of these you could not rule out.

## Define activation before measuring it

"Activation" is meaningless until someone writes down the event and the window.
It should be the action that best predicts a customer still being there in
ninety days, not the first thing they do.

Ask for the definition. If nobody has one, propose a candidate, say why, and
label it as provisional. Do not silently pick one.

The same applies to "active user". Daily, weekly and monthly actives depend
entirely on what counts as an action. A login is usually a bad choice; a session
that includes the core action is usually better.

## The questions worth asking of the join

| Question | Signal |
|---|---|
| Paying accounts with declining usage | The strongest churn predictor billing data cannot see |
| New accounts that never reach activation | Onboarding failure, visible weeks before it becomes churn |
| Accounts at seat limits with rising usage | Expansion opportunity |
| Revenue growing while adoption flattens | Monetising existing customers harder rather than growing |
| Adoption growing while revenue flattens | Value delivered and not captured |
| Feature adoption by plan tier | Whether packaging matches behaviour |

The first is where most of the value is. A paying account whose weekly usage
halved over six weeks is the call to make this week.

## Retention curves, carefully

- **Cohort by signup or by first activation**, and say which. They give very
  different curves.
- **A retention curve that has not flattened is not yet a retention curve.**
  Do not extrapolate it into LTV.
- **Incomplete cohorts.** The most recent cohort has not had time to churn.
  Never put it on the same chart as complete ones without marking it.
- **Survivorship.** Retention among accounts that survived to month six is not
  retention.

## Never

- **Ask for a credential** in chat or as a command argument. See
  **Credentials** above.
- **Send an event or write to the product.** Read only.
- **Pull raw user-level event streams into context.** They are enormous and
  usually contain personal data. Aggregate first, in SQL, then look.
- **Include personal data in output.** Event payloads carry emails, names, IPs,
  URLs with tokens, and sometimes more. Mask or aggregate before it reaches a
  summary.
- **Treat an event property as trustworthy** because it exists. Check the fill
  rate before segmenting on it.

## Correlation is not cause

Usage falling before churn is a hypothesis with a date on it, and it is a good
one. It is still not a cause. Say what evidence would settle it: an experiment,
a holdout, or asking the customers.

Report the relationship, the strength, the sample size, and what you cannot rule
out. A small sample deserves both readings: "three of eleven at-risk accounts
churned" is 27% and is also three accounts.

## Reference

- Revenue side of the join: [../revenue-analytics/SKILL.md](../revenue-analytics/SKILL.md)
