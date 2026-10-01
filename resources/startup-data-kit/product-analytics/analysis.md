# Answering product analytics questions

> **Upstream documentation wins.** Where this file disagrees with the [Bruin
> docs](https://getbruin.com/docs/bruin/overview.html), `bruin --help`, or
> PostHog, Mixpanel, Amplitude or Firebase documentation, those are right and
> this file is stale. Written against Bruin CLI `v0.11.765`, checked 2026-10-01.
> The product analytics tool's own UI is the reference you reconcile against,
> not this file.

Read this once a product analytics pipeline exists and the user is asking
questions of it. If `decisions.md` sits beside the pipeline's `pipeline.yml`,
read it first: it records the identity key, the activation definition and the
events this model counts. The `Never` rules in `SKILL.md` apply here too.

Event data is the one source that can explain *why* revenue moved. It is also
the one where the data you need most often turns out never to have been
captured.

## Before answering any product question

1. **Read the model before querying it.** Asset descriptions state the grain
   and what is excluded. Do not infer meaning from column names.
2. **Prefer report tables over raw tables.** On `posthog-bigquery`, read the
   `posthog_reports` assets first, and respect their guard columns:
   `is_complete_week` on retention, `is_reportable` and `was_enabled` on feature
   adoption.
3. **Check freshness first.** Read the last runs from Bruin Cloud MCP or
   `bruin cloud runs list --output json`, then the maximum event date in the
   raw table. A missing recent load reads as a usage drop.

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

**Check a property's fill rate before segmenting on it.** A property is not
trustworthy because it exists.

## Define activation before measuring it

"Activation" is meaningless until someone writes down the event and the window.
It should be the action that best predicts a customer still being there in
ninety days, not the first thing they do.

Ask for the definition. If nobody has one, propose a candidate, say why, and
label it as provisional. Do not silently pick one. Record it in `decisions.md`.

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

## When an event count looks wrong

1. **Check the run and freshness**, as above.
2. **Check how the history was loaded.** On `posthog-bigquery`, a backfill of
   `posthog_raw.events` covering more than one day per run silently returns
   partial data. Compare daily counts in the raw table against the PostHog UI
   before blaming the model.
3. **Check instrumentation**, as above: when the event shipped, and whether it
   was renamed.

If the model and the source genuinely disagree, show the gap. Do not adjust a
model to match a number someone expected.

## Correlation is not cause

Usage falling before churn is a hypothesis with a date on it, and it is a good
one. It is still not a cause. Say what evidence would settle it: an experiment,
a holdout, or asking the customers.

Report the relationship, the strength, the sample size, and what you cannot rule
out. A small sample deserves both readings: "three of eleven at-risk accounts
churned" is 27% and is also three accounts.

For the revenue side of the join, see the `revenue-analytics` skill.
