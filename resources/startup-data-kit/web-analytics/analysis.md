# Answering web analytics questions

> **Upstream documentation wins.** Where this file disagrees with the [Bruin
> docs](https://getbruin.com/docs/bruin/overview.html), `bruin --help`,
> Google's GA4 and Search Console documentation, or the GA4 property's own
> settings, those are right and this file is stale. Written against Bruin CLI
> `v0.11.766`, checked 2026-10-01.

Read `decisions.md` beside the pipeline's `pipeline.yml` first. The Never rules
in [SKILL.md](SKILL.md) apply.

## Before answering

- Read the report and staging assets, and the README's "Scope and limitations", before writing SQL; build on staging, not the raw exports.
- Check freshness: the last runs (Bruin Cloud MCP or `bruin cloud runs list`), then the maximum date in staging.
- State the surface (GA4 export, GA4 API or Search Console), the window and the definition with every number.
- Pin users, sessions, engaged sessions, key events and channel grouping from `decisions.md`, or ask; GA4 bounce rate is the inverse of engagement rate.

## Traps

- The GA4 API and the BigQuery export disagree, and GA4 sessions are not Universal Analytics sessions; explain the gap, do not fix it.
- Thresholding and sampling mean API breakdowns may not sum to totals; check whether a response was sampled.
- Consent mode and ad blockers undercount, far more for a technical B2B audience.
- Search Console clicks will not equal GA4 organic sessions; anonymised queries count in totals but not query rows; never average average position.
- GA4 takes 24 to 48 hours to settle, and Search Console lags two to three days and revises past days; leave recent days out of comparisons.
- The average of daily rates is not the rate; sum numerators and denominators.

## What this data cannot tell you

- Why traffic dropped, until a tracking change, deploy, consent banner or bot spike is ruled out.
- Whether a campaign worked; that needs an experiment or holdout.
- Revenue by landing page, channel or keyword, without a signup form storing landing page and channel on the account; otherwise answers stop at traffic.
- Search history beyond Search Console's roughly 16 months, unless it was loaded earlier.
