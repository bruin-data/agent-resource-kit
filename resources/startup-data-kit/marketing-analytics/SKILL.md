---
name: marketing-analytics
description: Use when analysing advertising spend, CAC, ROAS, attribution, campaign performance, email and lifecycle marketing, or CRM pipeline data from Google Ads, Meta, TikTok, LinkedIn, HubSpot, Klaviyo, Salesforce or similar, and when joining marketing spend to revenue.
---

# Marketing analytics

**Status:** experimental · **Risk:** read-only

> **Upstream documentation wins.** Where this file disagrees with the [Bruin
> docs](https://getbruin.com/docs/bruin/overview.html) or with an ad platform's
> own documentation, those are right and this file is stale. Ad platform metric
> definitions and attribution windows change often and without notice; check
> them rather than trusting a description here. Written against Bruin CLI
> `v0.11.765`, checked 2026-09-30.

Marketing data is the easiest place to produce a number that is precise,
well presented, and meaningless. Attribution is a modelling choice, not a
measurement, and the main job here is keeping that visible.

Setup is in the `bruin-agent` skill. This assumes a project exists.

## Look it up live

This file says what to reach for and what to be careful about. For the facts
themselves, ask the tool, and tell the user if it disagrees with this file:

- **Flags:** `bruin <command> --help`. The docs lag the CLI.
- **Docs:** the local Bruin MCP server, `bruin_get_doc_content('<path>')`, or
  `https://getbruin.com/docs/bruin/<path>.html` without it. For this skill:
  `bruin_get_docs_tree` (the `ingestion/` section) for which ad, lifecycle, CRM
  and support sources exist, `ingestion/<source>` (for example
  `ingestion/google-ads`) for a source's tables and connection fields, and
  `getting-started/templates-docs/ecommerce-README` for the `ecommerce`
  template. Page names can differ from the connection type key (`google-ads` is
  `googleads`).
- **The user's environment:** Bruin Cloud MCP, or
  `bruin cloud ... --output json`.

**Credentials.** Never ask for one in chat or pass one as a command argument.
For a source, the user runs `bruin connections add` with no flags (the
interactive prompt; its flag mode puts the secret on the command line) or
references `${VAR}` in `.bruin.yml`. For Cloud, `bruin cloud login` or an
exported `BRUIN_CLOUD_API_KEY`, never `--api-key`. `bruin auth status` shows
which is active without printing it.

## Sources

Bruin ingests ad platforms, mobile attribution, email and lifecycle tools, CRMs,
and support tools (useful as a churn signal). Check the docs tree for the
current list rather than assuming a connector exists or does not.

Run `bruin init --help` for templates. Most of these sources have none:
ingestion is supported, the modelling is yours.

The `ecommerce` template is not a general marketing template. It always
includes Shopify, takes Stripe or Shopify Payments, and supports Facebook,
Google and TikTok ads only. Read its README before recommending it. If the user
is on it, read `rpt_marketing_roi` before quoting it: as checked, its
`attributed_revenue` joins paid orders to web sessions on date alone, so each
day's paid revenue is counted against every channel with sessions that day, once
per session row. That is not an attribution model, and its `roas` inherits the
problem. Read the SQL in the user's copy, since the template may have changed.

## Start with one platform, not all of them

Connecting five ad platforms before any of them reconciles produces a dashboard
nobody trusts. Get one platform matching its own UI first, then add the next.

Ask which platform carries most of the spend and start there.

## The numbers only mean something together

Spend alone is an expense report. These are the joins that make it analysis:

| Question | Needs |
|---|---|
| CAC by channel | Ad spend joined to new customers from billing |
| ROAS | Ad spend joined to revenue, over a stated window |
| Payback period | CAC joined to the revenue curve per cohort |
| Which channel brings customers who stay | Acquisition channel carried through to retention |
| Pipeline conversion | CRM stages joined to closed revenue |

Every one of these crosses into another source. If the identity join does not
exist, that is the work, not a detail of it. Say so rather than producing a
number from whichever side happens to be available.

## Attribution is a choice, so name it

Platform-reported conversions do not agree with each other and do not agree with
your billing data. This is expected, not a bug.

- **Each platform claims credit for the same conversion.** Sum them and you get
  more conversions than you had customers. Never add conversions across
  platforms.
- **Attribution windows differ per platform and are configurable.** A 7-day
  click window and a 28-day window are different questions.
- **View-through conversions** inflate platform numbers relative to anything
  you can verify yourself.
- **iOS ATT and cookie loss** mean platform attribution degraded years ago.

State which attribution model is in use with any channel-level claim: platform
reported, last touch, first touch, or self-reported at signup. Say when the
model cannot settle a question, and say what would.

Self-reported attribution ("how did you hear about us") is unfashionable and
often the most honest signal available for early-stage companies.

## Currency, timezone and cost definitions

Small things that cause persistent unexplained gaps:

- **Currency.** Ad platforms report in the account currency. Decide the
  conversion policy, same as for revenue.
- **Timezone.** Platforms report in the ad account's timezone, which is often
  not the warehouse timezone or the billing timezone. A daily join across two
  timezones is off by a partial day, every day.
- **Cost basis.** Is spend gross or net of platform fees, agency fees, credits
  and rebates? Say which.
- **Refunds.** ROAS on gross revenue and ROAS on net revenue are different
  numbers.

## Traps worth checking before reporting

- **Averaging rates.** The average of daily CTRs is not the CTR. Sum the
  numerators and denominators, then divide.
- **Comparing periods of different length.** A 28-day month against a 31-day
  month is a 10% difference before anything happened.
- **Small denominators.** A campaign with 40 clicks and 2 conversions has a 5%
  conversion rate and also almost no information. Report the denominator.
- **Late attribution.** Recent days are undercounted because conversions are
  still landing. Never compare an incomplete recent window against a complete
  older one without labelling it.
- **Renamed campaigns.** A renamed campaign looks like one ending and another
  starting. Join on ID, not name.

## Never

- **Ask for a credential** in chat or as a command argument. See
  **Credentials** above.
- **Write to an ad platform.** Pausing a campaign, changing a budget or sending
  an email is a write with immediate money and reputation consequences. Read
  only. Propose the change and let a person make it.
- **Send marketing email.** Even a test. Stop and ask.
- **Pull contact lists into context.** Names, emails and phone numbers are rarely
  needed for analysis. Aggregate or use identifiers.

## What this data cannot tell you

| Asked | Actually needed |
|---|---|
| "Which channel caused this growth?" | An experiment or a holdout. Correlated spend and growth is a hypothesis. |
| "Should we cut this channel?" | Incrementality, not attributed ROAS. A channel can score well and be claiming credit for customers who would have arrived anyway. |
| "Why did CPMs rise?" | Usually auction dynamics you cannot see. Say so rather than inventing a reason. |
| "What is our true CAC?" | A decision about which costs count: paid only, plus salaries, plus tooling. Ask. |
