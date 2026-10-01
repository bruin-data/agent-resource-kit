---
name: ai-search-visibility
description: Use when a startup wants SEO, GEO or AEO visibility set up or answered. Sets up Search Console data or AI crawler logs, says where Bruin has no connector, and answers classic search, AI answer and AI crawler questions.
---

# Search and AI answer visibility

**Status:** experimental · **Risk:** approval-required

> **Upstream documentation wins.** Where this file disagrees with the [Bruin
> docs](https://getbruin.com/docs/bruin/overview.html), `bruin --help`,
> Google's Search Console documentation, or a measurement tool's own
> documentation, those are right and this file is stale. Written against Bruin
> CLI `v0.11.766`, checked 2026-10-01.

Sets up data for whichever of three questions the user has (ranking in classic
search, appearing in AI answers, or AI crawlers fetching the site) and answers
from it. It exists to prevent sampled or inferred AI visibility being presented
as measured.

## Set up

Follow [workflow.md](workflow.md).

> **Important: do not ask a fixed list of questions.** Read the template as it
> is today and work out which of its choices this user needs to confirm.
> Templates change, so the questions change with them.

**Templates:** `google-web-analytics` for SEO, none for AI visibility; confirm
with `bruin init --help`. Otherwise read `ingestion/gsc`, or `ingestion/s3` or
`ingestion/gcs` for crawler logs; the modelling is theirs to build. AI answer
visibility comes only from a third-party sampling tool such as Peec AI, set up
in that tool.

**Watch for:**

- `google-web-analytics` is BigQuery only and ingests nothing: it needs the GA4 streaming export and the Search Console bulk export running, and neither backfills.
- `ingestion/gsc` reaches back roughly 16 months.
- Logs load only as CSV, JSONL or Parquet.
- If AI answer visibility is the only question, no Bruin pipeline is needed; say so.

**Usually needs the user's input:**

- Which of the three questions; often more than one.
- Search Console properties: Domain or URL-prefix, and whether subdomains or a blog are separate; the service account must be a user on each.
- Brand and competitor names; branded demand measures awareness, not SEO work.
- Which paths are product, content, docs or support, and any meaningful query parameters or locale prefixes.
- Whether assistant referrers (`chatgpt.com`, `perplexity.ai`) get their own channel.
- Which log source exists, where it writes, its format and its retention; expired logs leave the warehouse as the only copy.
- The sampling tool's prompt set, competitors and assistants; any change moves the score.

**Reconcile against:** Search Console's property-level clicks and impressions
for a window ending at least three days ago, and one day of crawler log rows
against the CDN's own request analytics; a sampling tool has nothing to
reconcile, so quote its dashboard with prompt set and dates.

## Answer questions

Read [analysis.md](analysis.md).

## Never

- Ask for or print a credential; write, run, backfill, `--full-refresh` or
  touch production without a yes; put personal data in output.
- Publish content to a CMS, repository or live site; draft it and let a person publish.
- Change `robots.txt` or crawler directives without explicit approval.
