---
name: web-analytics
description: Use when a startup wants web analytics set up or answered. Walks the user through installing Bruin, turning on the GA4 and Search Console exports to BigQuery, and choosing and customising the google-web-analytics template or GA4 and Search Console ingestion to their site, then answers traffic, landing page, channel, conversion and funnel questions from it, including joins to signups and revenue.
---

# Web analytics

**Status:** experimental · **Risk:** approval-required

> **Upstream documentation wins.** Where this file disagrees with the [Bruin
> docs](https://getbruin.com/docs/bruin/overview.html), `bruin --help`, or
> Google's GA4 and Search Console documentation, those are right and this file
> is stale. GA4 definitions in particular are configurable per property, so the
> property's own settings beat any general description here. Written against
> Bruin CLI `v0.11.765`, checked 2026-10-01.

Two jobs. **Set up:** work with the user to install a maintained Bruin web
analytics template and customise it to their site and property. **Answer:**
questions from what it built, in [analysis.md](analysis.md).

GA4 is the source people most often quote and least often reconcile. Most of the
damage is done during setup: a key event that is never sent, a subdomain left
out, a property timezone nobody checked. Each one fails silently, as an empty
column or a quietly wrong total.

## Look it up live

This file says what to reach for and what to be careful about. For the facts
themselves, ask the tool, and tell the user if it disagrees with this file:

- **Flags:** `bruin <command> --help`. The docs lag the CLI.
- **Docs:** the local Bruin MCP server, `bruin_get_doc_content('<path>')`, or
  `https://getbruin.com/docs/bruin/<path>.html` without it. For this skill:
  `getting-started/templates-docs/google-web-analytics-README` for what the
  template needs, builds and cannot do, `ingestion/google_analytics` for the GA4
  API connector, `ingestion/gsc` for the Search Console connector, its tables
  and metrics, and `platforms/bigquery` for the warehouse connection.
- **The user's environment:** Bruin Cloud MCP, or
  `bruin cloud ... --output json`.

## Setting it up

Follow [workflow.md](workflow.md) from the top: install, MCP, repository,
warehouse, template, credentials, then the questions. It is the same process
for every skill in this kit. What is specific to web analytics is below.

> **Important: do not ask a fixed list of questions.** Read the template as it
> is today and work out which of its choices this user needs to confirm.
> Templates change, so the questions change with them. Workflow step 7 says how.

### Templates to consider

Ask which sites they track, whether they use GA4 and Search Console, and
whether either already exports to BigQuery. Then check `bruin init --help`; at
the time of writing the one candidate was `google-web-analytics`.

Caveats to raise before recommending it:

- **It ingests nothing.** It reads the GA4 BigQuery export and the Search
  Console bulk data export where they already land, so it needs BigQuery and
  both exports running.
- **It reads only `events_intraday_*`.** That needs the GA4 export with
  streaming on. Without streaming every GA4 model is empty, with no error. The
  README has a query that checks which tables the property produces. Run it
  before the first run.
- **Neither export backfills.** History starts the day each was switched on.
- **Its first run is a `--full-refresh`,** per the README, and changing its
  brand or path patterns later means rebuilding staging the same way. Name
  that when you ask.
- **Not on BigQuery, or no exports:** there is no template. Ingest through
  `ingestion/google_analytics` and `ingestion/gsc` into their warehouse, and
  agree with the user that the modelling is theirs to build.

Cloudflare Radar (`ingestion/cloudflare-radar`) is Internet-wide aggregate data,
not this site's traffic. Do not use it as a traffic or bot source.

**Prefer the BigQuery export over the API where it exists.** The GA4 export
gives event-level data with no sampling and no quota. The Reporting API applies
sampling on large properties, enforces quotas, and applies thresholding that
silently drops rows. If someone has the export, use it and say why.

### Steps only the user can do

These happen in Google's consoles, not in Bruin. Give the exact steps, using
the Google instructions the README and `ingestion/<source>` pages link to, then
wait until the user says each is done.

- **Turn on the exports:** the GA4 BigQuery link with streaming, and the Search
  Console bulk data export.
- **Grant access:** the BigQuery connection's credentials need read on both
  export datasets and write on the datasets the pipeline creates. If an export
  lives in another project, grant read there too.
- **On the API route:** add the service account as a user on the Search Console
  property, and enable the Search Console API in its Google Cloud project.

If the exports were only just switched on, say that there is nothing to report
on yet. Check that the export tables exist and hold rows before the first run.

### What usually matters here

A lens for reading the template, not a script. For each, find what the template
does, then ask only where this site makes it matter. The definitions table in
[analysis.md](analysis.md) explains the GA4 terms.

- **Property and data streams:** which GA4 property, and which of its streams
  are this site.
- **Sites and hostnames:** which domains and subdomains count, and whether a
  docs or blog subdomain is a separate page from the marketing site. Whether
  any URL query parameters carry meaning.
- **Search Console properties:** Domain or URL-prefix, and how many.
- **Timezone and currency:** the property's own, against the warehouse and the
  billing system. Search Console dates are Pacific Time.
- **Key events:** which events count as conversions, whether the property
  actually sends them, and what each is worth if revenue lands elsewhere.
- **Sessions and channels:** the property's session and engagement settings,
  and default or custom channel grouping.
- **Internal and bot traffic:** internal traffic filters, staff and test
  traffic, and known bots.
- **Brand and page roles:** which queries are branded, and which paths are
  existing customers (docs, help) rather than prospects.
- **History:** how far back it matters, and when each export started.

### Reconcile against

The GA4 interface for sessions and users, and the Search Console interface for
clicks and impressions, over the same settled window. Use a full week or month
that ended at least three days ago: GA4 takes 24 to 48 hours to settle and
Search Console lags two to three days. Compare Search Console against a
property-level table, not one summed across pages.

Expect documented differences, not zero. The README's "Scope and limitations"
says which figures it matched and where the gaps are. GSC clicks will not equal
GA4 organic sessions. Record each gap in `decisions.md`.

## Answering questions afterwards

Read [analysis.md](analysis.md): what to check before answering, why GA4
numbers will not match each other, how Search Console differs, and what this
data cannot tell you. If the user is on a template, read its report assets and
"Scope and limitations" before writing any SQL. Rebuilding that logic inline is
how two answers to the same question start to differ.

## Never

- **Ask for a credential** in chat or as a command argument. A Google service
  account key is a private key. If offered one, say not to send it and to
  rotate it if already sent. Workflow step 6 has the safe path.
- **Print a credential**, including in errors, summaries and generated files.
- **Run against production** unless asked by name. Say which environment you used.
- **Pull URL-level data without checking for tokens.** Query strings contain
  session tokens, password reset links and personal data. Strip parameters
  before anything reaches a summary.
- **Treat IP or user-agent data as anonymous.** It is personal data in most
  jurisdictions.
- **Pull raw event or user records into context** when an aggregate answers the
  question.
- **Write without asking.** Installing, initialising, editing configuration or
  models, and running a pipeline all wait for the user's yes.

Stop and ask before any write to a source system, outbound message,
publication, credential change, production access, `--full-refresh` or backfill.
On this template, `--full-refresh` rebuilds staging from whatever the export
datasets still hold, and rescans them. Name that consequence and the expected
scan.

## Unverified

- **GA4 API access.** `ingestion/google_analytics` does not say what access the
  service account needs on the GA4 property. Google's Data API documentation
  is expected to require adding it as a user on the property. Read that page
  and the connector's error output before telling the user it is done.
