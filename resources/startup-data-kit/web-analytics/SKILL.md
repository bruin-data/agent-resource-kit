---
name: web-analytics
description: Use when analysing website traffic, sessions, landing page performance, acquisition channels, conversion rates or funnel drop-off from Google Analytics 4 or Google Search Console, and when joining web traffic to signups and revenue.
---

# Web analytics

**Status:** experimental · **Risk:** read-only

> **Upstream documentation wins.** Where this file disagrees with the [Bruin
> docs](https://getbruin.com/docs/bruin/overview.html) or with Google's GA4 and
> Search Console documentation, those are right and this file is stale. GA4
> definitions in particular are configurable per property, so the property's
> own settings beat any general description here. Written against Bruin CLI
> `v0.11.765`, checked 2026-09-30.

GA4 is the source people most often quote and least often reconcile. Sessions,
users and conversions all mean something specific and none of them mean what the
plain English word suggests.

Setup is in the `bruin-agent` skill. This assumes a project exists.

## Look it up live

This file says what to reach for and what to be careful about. For the facts
themselves, ask the tool, and tell the user if it disagrees with this file:

- **Flags:** `bruin <command> --help`. The docs lag the CLI.
- **Docs:** the local Bruin MCP server, `bruin_get_doc_content('<path>')`, or
  `https://getbruin.com/docs/bruin/<path>.html` without it. For this skill:
  `getting-started/templates-docs/google-web-analytics-README` for what the
  template needs, builds and cannot do, `ingestion/google_analytics` for the GA4
  API connector, and `ingestion/gsc` for the Search Console connector, its
  tables and metrics.
- **The user's environment:** Bruin Cloud MCP, or
  `bruin cloud ... --output json`.

**Credentials.** Never ask for one in chat or pass one as a command argument.
For a source, the user runs `bruin connections add` with no flags (the
interactive prompt; its flag mode puts the secret on the command line) or
references `${VAR}` in `.bruin.yml`. For Cloud, `bruin cloud login` or an
exported `BRUIN_CLOUD_API_KEY`, never `--api-key`. `bruin auth status` shows
which is active without printing it.

## Sources and where to start

- **GA4 and Search Console exports already in BigQuery:** the
  `google-web-analytics` template. Read its README first. It needs the GA4
  export with streaming on, because it reads only `events_intraday_*`; without
  streaming every GA4 model is empty, with no error. It also needs the Search
  Console bulk data export. Neither export backfills, so history starts the day
  each was switched on.
- **GA4 through the API:** read `ingestion/google_analytics` for the connection
  fields.
- **Search Console through the API:** read `ingestion/gsc`. The service account
  has to be added as a user on the Search Console property, and the API enabled
  in its Google Cloud project, before anything loads.

Cloudflare Radar (`ingestion/cloudflare-radar`) is Internet-wide aggregate data,
not this site's traffic. Do not use it as a traffic or bot source.

**Prefer the BigQuery export over the API where it exists.** The GA4 export
gives event-level data with no sampling and no quota. The Reporting API applies
sampling on large properties, enforces quotas, and applies thresholding that
silently drops rows. If someone has the export, use it and say why.

## GA4 numbers will not match, and that is normal

Do not treat a mismatch as a bug to fix. Explain it.

- **The API and the BigQuery export disagree.** Different processing, different
  attribution, different session definitions. Both are "GA4".
- **GA4 sessions differ from Universal Analytics sessions.** Any year-over-year
  comparison crossing the migration is comparing two different metrics.
- **Consent mode and ad blockers** mean GA4 undercounts, by a share that varies
  by audience. A technical B2B audience blocks far more than a consumer one.
- **Thresholding** suppresses rows with small counts when Google Signals is on.
  Totals will not equal the sum of a breakdown.
- **Sampling** applies to large API queries. Check whether a response was
  sampled before quoting it.
- **Timezone** is the property's, which may differ from the warehouse and the
  billing system.

State which surface a number came from, every time. On the
`google-web-analytics` template, also read "Scope and limitations" in its
README before quoting a number; it lists the template's own gaps.

## Definitions to pin down before reporting

| Term | The question to ask |
|---|---|
| Users | Active users, total users or new users? GA4 reports several and defaults vary by report. |
| Sessions | 30 minute inactivity timeout by default, and also ends at midnight and on a campaign change. Configurable. |
| Engaged session | Over 10 seconds, or a conversion, or 2+ pageviews. The threshold is configurable. |
| Bounce rate | In GA4 this is the inverse of engagement rate, not the UA definition. |
| Conversion | Whatever was configured as a key event. Check what is actually counted. |
| Channel grouping | Default or custom? Rules differ and both are called "channel". |

## Search Console is a different dataset, not a subset

- **No sessions, no conversions.** `ingestion/gsc` lists what it does carry.
- **GSC clicks will not equal GA4 organic sessions.** Different measurement
  points, different filtering, different bot handling. Expect a gap and do not
  reconcile them to zero.
- **Position is an average**, weighted oddly, and an average of averages across
  queries is not meaningful.
- **Anonymised queries** are excluded from the query dimension but included in
  totals, so query-level rows will not sum to the total.
- **Limited history.** Search Console keeps roughly 16 months. Load it into
  the warehouse if longer matters.
- **Recent days are missing, and past days change.** Search Console lags two to
  three days and revises history in place. Reload a trailing window rather than
  only appending, and leave the last three days out of any comparison.

## The join that makes it useful

Web analytics alone reports traffic. Joined to billing, it reports acquisition:

| Question | Needs |
|---|---|
| Which landing pages produce paying customers | Landing page to signup to revenue |
| Which channels bring customers who stay | Channel joined through to retention |
| Where the funnel actually leaks | Session to signup to activation to payment |
| Whether an SEO investment paid back | GSC clicks to signups over a stated window |

The join key is the hard part. It usually means a signup form capturing the
landing page and channel, stored on the account. If that does not exist, say
that the join is the work, and that GA4-only answers stop at traffic.

## Traps

- **Averaging rates.** The average of daily conversion rates is not the
  conversion rate. Sum numerators and denominators.
- **Recent days are incomplete.** GA4 data can take 24 to 48 hours to settle.
  Never compare an incomplete window to a complete one without labelling it.
- **Bot traffic.** GA4 filters known bots, not all of them. A traffic spike with
  no downstream effect is usually not people.
- **Site changes look like behaviour changes.** A redesign, a URL change or a
  new consent banner shifts every metric at once. Check the deploy log before
  inventing a story.
- **Seasonality.** Compare like periods, and say which.

## Never

- **Ask for a credential** in chat or as a command argument. A Google service
  account key is a private key. See **Credentials** above.
- **Pull URL-level data without checking for tokens.** Query strings contain
  session tokens, password reset links and personal data. Strip parameters
  before anything reaches a summary.
- **Treat IP or user-agent data as anonymous.** It is personal data in most
  jurisdictions.

## What this data cannot tell you

| Asked | Actually needed |
|---|---|
| "Why did traffic drop?" | Check for a tracking change, a deploy or a consent banner first. Those explain most drops. |
| "Did this campaign work?" | An experiment or holdout. Traffic correlating with a launch is a hypothesis. |
| "What is our real conversion rate?" | A decision about the denominator: all sessions, new sessions, or qualified traffic. Ask. |
| "Which keyword drives revenue?" | Keyword-level revenue attribution, which GSC cannot provide. See `ai-search-visibility`. |

## Reference

- Search visibility: [../ai-search-visibility/SKILL.md](../ai-search-visibility/SKILL.md)
