---
name: marketing-analytics
description: Use when a startup wants marketing analytics set up or answered. Walks the user through installing Bruin, choosing a template or ingesting their ad, email and CRM sources (Google Ads, Meta, TikTok, LinkedIn, HubSpot, Klaviyo, Salesforce), customising attribution, currency, timezone and cost definitions to their business, then answers CAC, ROAS, attribution and campaign questions from it.
---

# Marketing analytics

**Status:** experimental · **Risk:** approval-required

> **Upstream documentation wins.** Where this file disagrees with the [Bruin
> docs](https://getbruin.com/docs/bruin/overview.html), `bruin --help`, or an ad
> platform's own documentation, those are right and this file is stale. Ad
> platform metric definitions and attribution windows change often and without
> notice; check them rather than trusting a description here. Written against
> Bruin CLI `v0.11.765`, checked 2026-10-01. Each platform's own spend report is
> the reference you reconcile against, not this file.

Two jobs. **Set up:** work with the user to ingest their marketing sources, on a
maintained Bruin template where one fits, and customise it to how this business
buys and counts. **Answer:** questions from what it built, in
[analysis.md](analysis.md).

Attribution is a modelling choice, not a measurement. The failure mode is a
precise, well presented ROAS that means nothing. Most of it is prevented during
setup, by asking the user what the model would otherwise assume.

## Look it up live

This file says what to reach for and what to be careful about. For the facts
themselves, ask the tool, and tell the user if it disagrees with this file:

- **Flags:** `bruin <command> --help`. The docs lag the CLI.
- **Docs:** the local Bruin MCP server, `bruin_get_doc_content('<path>')`, or
  `https://getbruin.com/docs/bruin/<path>.html` without it. For this skill:
  `bruin_get_docs_tree` (the `ingestion/` section) for which ad, lifecycle, CRM
  and attribution sources exist, `ingestion/<source>` (for example
  `ingestion/google-ads`, `ingestion/facebook-ads`) for a source's tables and
  connection fields, `getting-started/templates-docs/ecommerce-README`,
  `ingestion/frankfurter` for FX rates, and `quality/overview`. Page names can
  differ from the connection type key (`google-ads` is `googleads`).
- **The user's environment:** Bruin Cloud MCP, or
  `bruin cloud ... --output json`.

## Setting it up

Follow [workflow.md](workflow.md) from the top: install, MCP, repository,
warehouse, template, credentials, then the questions. It is the same process
for every skill in this kit. What is specific to marketing is below.

> **Important: do not ask a fixed list of questions.** Read the template as it
> is today and work out which of its choices this user needs to confirm.
> Templates change, so the questions change with them. Workflow step 7 says how.

### Templates to consider

Ask which ad platforms they spend on, and which carries most of the spend. Ask
which email or lifecycle tool and which CRM they use, and where revenue lives,
since CAC and ROAS need it. Start with the biggest platform and get it
reconciling before adding the next.

Then check `bruin init --help`. Few templates cover marketing. At the time of
writing, only `ecommerce` modelled ad spend. Caveats the README will not flag:

- **`ecommerce`** always includes Shopify. Its wizard offers ClickHouse,
  BigQuery or Snowflake; Shopify Payments or Stripe; Klaviyo or HubSpot;
  Facebook, Google and TikTok ads; GA4 or Mixpanel. It is not a general
  marketing template. Without Shopify it does not fit.
- **The wizard needs an interactive terminal.** `bruin init ecommerce` fails
  without one. Give the user the command and let them answer its prompts, then
  read what it generated.
- **Its `rpt_marketing_roi` is not attribution.** As checked in `v0.11.765`, it
  joins paid orders to web sessions on date alone, so its `attributed_revenue`
  and `roas` overcount. `stg_marketing_spend` labels every ad platform
  `paid_ads`, while GA4 sessions from Google or TikTok land in `paid_search` or
  `other`. `cost_per_acquisition` sums platform-reported conversions across
  platforms. Show the user the SQL and agree a fix before anyone quotes it.
- **`demo-snowflake-salesforce`** is a demo. Its seed asset writes dummy records
  into Salesforce, and its first run uses `--full-refresh`. Never point it at
  the user's real org.
- **`google-web-analytics`** is organic search from GA4 and Search Console, with
  no ad spend. That is the `web-analytics` skill.

For anything else (LinkedIn, Reddit, Snapchat, Apple Ads, AppsFlyer, Adjust,
HubSpot, Salesforce, Klaviyo without Shopify), read `ingestion/<source>`.
Ingesting it is easy; the channel mapping, attribution and join to revenue are
the work. Say that no template fits, and agree the modelling with the user
before starting.

### What usually matters here

A lens for reading the template, not a script. For each, find what the template
or ingested source does, then ask only where this business makes it matter.
[analysis.md](analysis.md) explains why each one moves the number.

- **Attribution model and window:** platform reported, last touch, first touch,
  or self-reported at signup, and each platform's click and view windows.
- **Which conversions count:** platform-reported conversions, or new customers
  from billing. View-through in or out.
- **Channel mapping:** how sources, mediums and campaigns map to channels.
- **Currency:** each ad account's currency, and whether to convert or report per
  currency.
- **Timezone:** each ad account's timezone against the warehouse and billing.
- **Cost basis:** spend gross or net of platform fees, agency fees, credits and
  rebates.
- **Revenue basis:** ROAS on gross or net of refunds.
- **Identity join to revenue:** the shared identifier between ad, web and billing
  data (click ID, UTM, customer ID). If none exists, building it is the work.
- **What to exclude:** test or internal accounts, and campaigns or accounts that
  belong to another business line.
- **History and late conversions:** how far back matters, and whether the load
  re-reads recent days while conversions are still landing.

### Reconcile against

Each ad platform's own spend report for one recent full month, in the account's
currency and timezone. Reconcile spend first: it is deterministic. Platform
conversions will not match billing by design; compare new customers against the
billing system instead. Record each gap and its explanation.

## Answering questions afterwards

Read [analysis.md](analysis.md): what to check before answering, why platform
numbers disagree, and what marketing data cannot tell you. If the user is on a
template, read its report assets before writing any SQL. Rebuilding that logic
inline is how two answers to the same question start to differ.

## Never

- **Ask for a credential** in chat or as a command argument. If offered one, say
  not to send it and to rotate it if already sent. Workflow step 6 has the
  safe path.
- **Print a credential**, including in errors, summaries and generated files.
- **Write to an ad platform.** Pausing a campaign, changing a budget or sending
  an email is a write with immediate money and reputation consequences. Read
  only. Propose the change and let a person make it.
- **Send marketing email.** Even a test. Stop and ask.
- **Run against production** unless asked by name. Say which environment you used.
- **Pull contact lists into context.** Names, emails and phone numbers are rarely
  needed for analysis. Aggregate or use identifiers.
- **Write without asking.** Installing, initialising, editing configuration or
  models, and running a pipeline all wait for the user's yes.

Stop and ask before any write to a source system, outbound message,
publication, credential change, production access, `--full-refresh` or backfill.
Name what a `--full-refresh` replaces before asking.
