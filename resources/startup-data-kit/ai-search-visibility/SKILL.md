---
name: ai-search-visibility
description: Use when a startup wants SEO, GEO or AEO measurement set up or answered. Works out with the user which question they have (Search Console performance, appearing in AI assistant answers, or AI crawlers such as GPTBot and ClaudeBot fetching the site), sets up and customises the closest Bruin template or ingestion, says plainly where Bruin has no connector, then answers visibility and content questions from it.
---

# Search and AI answer visibility

**Status:** experimental · **Risk:** approval-required

> **Upstream documentation wins.** Where this file disagrees with the [Bruin
> docs](https://getbruin.com/docs/bruin/overview.html), `bruin --help`, Google's
> Search Console documentation, or a measurement tool's own documentation, those
> are right and this file is stale. This area moves faster than any other in
> this repository, so treat specifics here as a starting point rather than
> current fact. Written against Bruin CLI `v0.11.765`, checked 2026-10-01.

Two jobs. **Set up:** work with the user to get the data for the question they
actually have, from the closest Bruin template or ingestion, customised to this
site. **Answer:** questions from what it built, in [analysis.md](analysis.md).

Three overlapping things sit under this heading:

- **SEO**, ranking in classic search results. Mature, measurable, Search Console.
- **GEO / AEO**, appearing in AI-generated answers. New, measurable only through
  third-party sampling, and heavily hyped.
- **AI crawler traffic**, whether assistants are fetching the site at all.
  Measurable from server logs today.

They need different data and have very different evidence quality. Be straight
about which one a request is actually about.

## Look it up live

This file says what to reach for and what to be careful about. For the facts
themselves, ask the tool, and tell the user if it disagrees with this file:

- **Flags:** `bruin <command> --help`. The docs lag the CLI.
- **Docs:** the local Bruin MCP server, `bruin_get_doc_content('<path>')`, or
  `https://getbruin.com/docs/bruin/<path>.html` without it. For this skill:
  `getting-started/templates-docs/google-web-analytics-README` for the template,
  `ingestion/gsc` and `ingestion/google_analytics` for the Google connectors,
  `ingestion/s3` and `ingestion/gcs` for loading log files, and `ingestion/g2`
  and `ingestion/trustpilot` for review sites.
- **A sampling tool:** its own documentation or MCP server. It is not Bruin.
- **The user's environment:** Bruin Cloud MCP, or
  `bruin cloud ... --output json`.

## Setting it up

Follow [workflow.md](workflow.md) from the top: install, MCP, repository,
warehouse, template, credentials, then the questions. It is the same process
for every skill in this kit. What is specific to search and AI visibility is
below.

> **Important: do not ask a fixed list of questions.** Read the template as it
> is today and work out which of its choices this user needs to confirm.
> Templates change, so the questions change with them. Workflow step 7 says how.

Start by asking which of the three questions the user has. The answer decides
which path below applies, and whether a Bruin pipeline is needed at all.

### Templates to consider

There is no Bruin template for AI answer visibility. Check `bruin init --help`
for anything new, then match each question to a path:

| Path | SEO | AI answer visibility | AI crawler traffic |
|---|---|---|---|
| `google-web-analytics` template | Yes | No | No |
| `ingestion/gsc` alone | Yes, unmodelled | No | No |
| Logs through `ingestion/s3` or `ingestion/gcs` | No | No | Yes, unmodelled |
| A third-party sampling tool, such as Peec AI | No | Yes, sampled | No |

- **`google-web-analytics`** is BigQuery only and ingests nothing. It reads the
  GA4 BigQuery export and the Search Console bulk data export, which must
  already be running. Neither export backfills, so history starts the day each
  was enabled. It needs the GA4 streaming export (`events_intraday_*`); without
  it every GA4 model is silently empty. Read the README's scope section before
  the first run.
- **`ingestion/gsc`** reads the Search Console API into any warehouse, with
  roughly 16 months of history and no reports. Use it when the warehouse is not
  BigQuery, the bulk export is not enabled, or history before the export
  matters. The modelling is yours; agree that before starting.
- **Crawler logs** have no template. `ingestion/s3` and `ingestion/gcs` read
  CSV, JSONL and Parquet, gzipped or not. A log in any other shape needs
  converting before it loads. Classifying user agents is modelling you build.
- **AI answer visibility has no Bruin connector.** That measurement comes from
  third-party tools that sample assistant responses on a schedule. Set it up in
  the tool, following its own documentation. Say so rather than implying the
  pipeline can produce it. If this is the only question, no Bruin pipeline is
  needed.
- **Review sites:** `ingestion/g2` and `ingestion/trustpilot` load presence on
  sites assistants may cite. Ingestion only.
- **Cloudflare Radar** (`ingestion/cloudflare-radar`) is Internet-wide aggregate
  data, not this site's traffic or crawler logs. Use it for context only. Its
  docs page says runs fail until Bruin's pinned ingestr version includes it.

### What usually matters here

A lens for reading the template, not a script. For each, find what the template
or ingestion does, then ask only where this site makes it matter.

- **Which of the three questions:** often more than one, rarely all three.
- **Search Console properties:** Domain or URL-prefix, and whether subdomains
  or a separate blog are their own properties. The service account has to be
  added as a user on each property before anything loads.
- **Export state:** whether the GA4 and Search Console BigQuery exports are
  enabled, and since when.
- **Brand and competitor names:** branded demand measures awareness, not SEO
  work. Splitting it out changes every headline trend.
- **Site structure:** which paths are product, content, docs or support, and
  whether URLs carry meaningful query parameters or locale prefixes.
- **Outcomes after the click:** which events count, and how they are valued.
  Modelled value is not revenue.
- **Assistant referrals:** whether `chatgpt.com`, `perplexity.ai` and similar
  should be their own channel. Check how the template classifies channels.
- **Logs:** which source exists (CDN, origin server), where it writes, and in
  what format.
- **Log retention:** how long the bucket keeps logs. Once older logs expire,
  the warehouse is the only copy.
- **Which crawlers to track:** start from the list in
  [analysis.md](analysis.md), and check `robots.txt` before reading absence as
  a signal.
- **Sampling tool setup:** the prompt set, the competitors and the assistants
  sampled. A change to any of them moves the score.
- **History:** how far back it matters, and whether this path can reach it.

### Reconcile against

- **Search Console:** clicks and impressions in the Search Console interface
  for a settled window, excluding the last three days. Compare property-level
  totals, not URL or query rows, which do not sum to them.
- **Crawler logs:** row counts for one day against the CDN's or server's own
  request analytics for the same window and timezone.
- **Sampling tools:** nothing in Bruin to reconcile. Read the tool's own
  dashboard, and state its prompt set and date range with any number.

Record each gap and its explanation in `decisions.md`.

## Answering questions afterwards

Read [analysis.md](analysis.md): what Search Console can and cannot show, how to
report sampled AI visibility, what crawler logs measure, and which content work
has evidence behind it. If the user is on a template, read its report assets
before writing any SQL.

## Never

- **Ask for a credential** in chat or as a command argument. A Google service
  account key is a private key. If offered one, say not to send it and to rotate
  it if already sent. Workflow step 6 has the safe path.
- **Print a credential**, including in errors, summaries and generated files.
- **Run against production** unless asked by name. Say which environment you used.
- **Pull raw log rows or session records into context** when an aggregate
  answers the question.
- **Put a raw URL in output without stripping its parameters.** Query strings
  carry session tokens, reset links and personal data.
- **Publish content.** Drafting is fine; pushing to a CMS, a repository or a
  live site is a write. Propose it and let a person publish.
- **Change `robots.txt` or crawler directives** without explicit approval. A
  wrong line here can deindex a site.
- **Write without asking.** Installing, initialising, editing configuration or
  models, and running a pipeline all wait for the user's yes.

Stop and ask before any write to a source system, outbound message,
publication, credential change, production access, `--full-refresh` or backfill.
`--full-refresh` drops and recreates tables. On `google-web-analytics` the first
run and any change to a classification variable need one on staging; scope it
to the earliest export date and say the expected scan. On a log table whose
bucket has expired old files, it discards history the source no longer holds.
Name that consequence.
