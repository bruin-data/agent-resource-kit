---
name: marketing-analytics
description: Use when a startup wants marketing analytics set up or answered. Sets up ad, email and CRM sources (Google Ads, Meta, TikTok, LinkedIn, HubSpot, Klaviyo, Salesforce) and answers CAC, ROAS, attribution and campaign questions.
---

# Marketing analytics

**Status:** experimental · **Risk:** approval-required

> **Upstream documentation wins.** Where this file disagrees with the [Bruin
> docs](https://getbruin.com/docs/bruin/overview.html), `bruin --help`, or an ad
> platform's documentation, those are right and this file is stale. Written
> against Bruin CLI `v0.11.766`, checked 2026-10-01.

Sets up the user's ad, lifecycle and CRM sources, on a template where one fits,
and answers CAC, ROAS and campaign questions. It exists to prevent a precise,
well presented ROAS that means nothing: attribution is a modelling choice, not
a measurement.

## Set up

Follow [workflow.md](workflow.md).

> **Important: do not ask a fixed list of questions.** Read the template as it
> is today and work out which of its choices this user needs to confirm.
> Templates change, so the questions change with them.

**Templates:** `ecommerce`; confirm with `bruin init --help`. For anything else
(LinkedIn, Reddit, Snapchat, Apple Ads, AppsFlyer, Adjust, HubSpot, Salesforce,
Klaviyo without Shopify), read `ingestion/<source>`; the modelling is theirs to
build.

**Watch for:**

- `ecommerce` always includes Shopify; without Shopify it does not fit.
- `google-web-analytics` is organic search with no ad spend; that is `web-analytics`.

**Usually needs the user's input:**

- Attribution: platform reported, last touch, first touch or self-reported; click and view windows; platform conversions or new customers from billing.
- Channel mapping: how sources, mediums and campaigns map to channels.
- Currency and timezone of each ad account, against the warehouse and billing.
- Cost basis (gross or net of platform and agency fees, credits, rebates) and revenue basis (gross or net of refunds).
- Identity join to revenue: click ID, UTM or customer ID; if none exists, building it is the work.
- Exclusions: test or internal accounts, and campaigns from another business line.
- History, and whether the load re-reads recent days while conversions land.

**Reconcile against:** each ad platform's own spend report for one recent full
month, in the account's currency and timezone, biggest-spend platform first;
compare new customers against billing, not platform conversions.

## Answer questions

Read [analysis.md](analysis.md).

## Never

- Ask for or print a credential; write, run, backfill, `--full-refresh` or
  touch production without a yes; put personal data in output.
- Write to an ad platform (pause a campaign, change a budget) or send marketing email, even a test.
- Point `demo-snowflake-salesforce` at a real Salesforce org; its seed asset writes dummy records.
