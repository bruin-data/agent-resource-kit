# Answering product analytics questions

> **Upstream documentation wins.** Where this file disagrees with the [Bruin
> docs](https://getbruin.com/docs/bruin/overview.html), `bruin --help`, or
> PostHog, Mixpanel, Amplitude or Firebase documentation, those are right and
> this file is stale. Written against Bruin CLI `v0.11.766`, checked 2026-10-01.

Read `decisions.md` beside the pipeline's `pipeline.yml` first. The Never rules
in [SKILL.md](SKILL.md) apply.

## Before answering

- Read the report assets before writing SQL, and respect their completeness and reportability guard columns.
- Check freshness: the last runs (Bruin Cloud MCP or `bruin cloud runs list`), then the maximum event date in raw; a missing load reads as a usage drop.
- State source, window, the activation or "active" definition and the cohort basis with every number.
- Before joining usage to revenue, confirm the identity key exists and report the match rate; do not call the matched share the customer base.

## Traps

- An event never instrumented looks identical to one never done; adoption starting at zero often marks the day the event shipped.
- A renamed event looks like one feature dying and another being born.
- A property is not trustworthy because it exists; check its fill rate before segmenting.
- One account has many users, and anonymous, multi-device and sales-led identities may not be stitched.
- Cohort by signup or first activation and say which; mark incomplete recent cohorts; do not extrapolate an unflattened curve into LTV.
- Client-side events are lost to ad blockers, offline use and crashes; server-side counts are more complete.

## What this data cannot tell you

- Cause: usage falling before churn is a hypothesis; an experiment, a holdout or asking customers settles it. Give the sample size.
- Whether a feature that was never instrumented is used.
- History segmented by a property that was never captured.
