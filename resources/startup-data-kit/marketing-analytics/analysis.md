# Answering marketing questions

> **Upstream documentation wins.** Where this file disagrees with the [Bruin
> docs](https://getbruin.com/docs/bruin/overview.html), `bruin --help`, or an ad
> platform's own documentation, those are right and this file is stale. Ad
> platform metric definitions and attribution windows change often and without
> notice; check them rather than trusting a description here. Written against
> Bruin CLI `v0.11.765`, checked 2026-10-01.

Read this once a marketing pipeline exists and the user is asking questions of
it. If `decisions.md` sits beside the pipeline's `pipeline.yml`, read it first:
it records which attribution model, currency, timezone and cost basis this model
follows. The `Never` rules in `SKILL.md` apply here too.

Marketing data is the easiest place to produce a number that is precise, well
presented, and meaningless. Attribution is a modelling choice, not a
measurement, and the main job here is keeping that visible.

## Before answering any marketing question

1. **Read the model before querying it.** Asset descriptions and SQL say how
   channels are mapped and what is joined to what. Do not infer meaning from
   column names.
2. **Prefer report tables over raw tables**, after reading the report's SQL.
3. **Check freshness.** Read the last runs from Bruin Cloud MCP or
   `bruin cloud runs list --output json`, then the maximum date in each raw ad
   table. One platform failing to load reads as that channel's spend dropping.

If the user is on the `ecommerce` template, read `rpt_marketing_roi` before
quoting it. As checked against the template shipped with `v0.11.765`, its
`attributed_revenue` joins paid orders to web sessions on date alone, so each
day's paid revenue is counted against every channel with sessions that day, once
per session row. That is not an attribution model, and its `roas` inherits the
problem. Read the SQL in the user's copy, since the template may have changed
or been customised.

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

## What this data cannot tell you

| Asked | Actually needed |
|---|---|
| "Which channel caused this growth?" | An experiment or a holdout. Correlated spend and growth is a hypothesis. |
| "Should we cut this channel?" | Incrementality, not attributed ROAS. A channel can score well and be claiming credit for customers who would have arrived anyway. |
| "Why did CPMs rise?" | Usually auction dynamics you cannot see. Say so rather than inventing a reason. |
| "What is our true CAC?" | A decision about which costs count: paid only, plus salaries, plus tooling. Ask. |

Say what is missing and offer the concrete next step. Do not produce an
approximation without labelling it as one.
