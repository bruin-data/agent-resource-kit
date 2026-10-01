---
name: web-analytics
description: Use when a startup wants web analytics set up or answered. Sets up GA4 and Search Console data through the google-web-analytics template or ingestion and answers traffic, landing page, channel, conversion and funnel questions, including joins to signups and revenue.
---

# Web analytics

**Status:** experimental · **Risk:** approval-required

> **Upstream documentation wins.** Where this file disagrees with the [Bruin
> docs](https://getbruin.com/docs/bruin/overview.html), `bruin --help`,
> Google's GA4 and Search Console documentation, or the GA4 property's own
> settings, those are right and this file is stale. Written against Bruin CLI
> `v0.11.766`, checked 2026-10-01.

Sets up GA4 and Search Console data for this site and answers traffic,
channel, conversion and funnel questions from it. It exists to prevent setup
mistakes that fail silently: a key event never sent, a subdomain left out, a
property timezone nobody checked.

## Set up

Follow [workflow.md](workflow.md).

> **Important: do not ask a fixed list of questions.** Read the template as it
> is today and work out which of its choices this user needs to confirm.
> Templates change, so the questions change with them.

**Templates:** `google-web-analytics`; confirm with `bruin init --help`. Not on
BigQuery, or no exports: read `ingestion/google_analytics` and `ingestion/gsc`;
the modelling is theirs to build. Prefer the GA4 BigQuery export over the GA4
API where it exists. Cloudflare Radar is Internet-wide data, not this site's
traffic.

**Watch for:**

- It ingests nothing: it reads the GA4 BigQuery export and the Search Console bulk export, which the user must switch on first.
- It reads only `events_intraday_*`; without GA4 streaming export every GA4 model is empty, with no error.
- Neither export backfills; history starts the day each was switched on.
- Changing brand or path patterns later means rebuilding staging with `--full-refresh`.

**Usually needs the user's input:**

- Which GA4 property, and which of its data streams are this site.
- Which domains and subdomains count, and whether any query parameters carry meaning.
- Search Console properties: Domain or URL-prefix, and how many.
- Timezone and currency: the property's, against the warehouse and billing; Search Console dates are Pacific Time.
- Key events: which count as conversions, whether the property actually sends them, and their value.
- Session, engagement and channel grouping settings; internal, staff, test and bot traffic to exclude.
- Branded queries, and which paths (docs, help) are existing customers rather than prospects.

**Reconcile against:** GA4's interface for sessions and users and Search
Console's property-level clicks and impressions, over a full week or month that
ended at least three days ago.

## Answer questions

Read [analysis.md](analysis.md).

## Never

- Ask for or print a credential; write, run, backfill, `--full-refresh` or
  touch production without a yes; put personal data in output.
- Put a URL in output without stripping its query string; it carries session tokens and reset links.
- Treat IP or user-agent data as anonymous.

## Unverified

- What access a service account needs on a GA4 property for `ingestion/google_analytics`; read Google's Data API documentation and the connector's error output.
