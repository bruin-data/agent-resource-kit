---
name: support-analytics
description: Use when a startup wants customer support analytics set up or answered. Sets up the gorgias template or Zendesk, Intercom, Freshdesk or HubSpot ingestion and answers ticket volume, response and resolution time, CSAT, backlog and contact reason questions.
---

# Support analytics

**Status:** experimental · **Risk:** approval-required

> **Upstream documentation wins.** Where this file disagrees with the [Bruin
> docs](https://getbruin.com/docs/bruin/overview.html), `bruin --help`, or
> Gorgias, Zendesk, Intercom, Freshdesk or HubSpot documentation, those are
> right and this file is stale. Written against Bruin CLI `v0.11.766`, checked
> 2026-10-01.

Sets up a helpdesk pipeline and answers support questions from it. It exists to
prevent a response time measured from a different clock than the support
lead's, or a ticket volume that includes spam and auto-replies.

## Set up

Follow [workflow.md](workflow.md).

> **Important: do not ask a fixed list of questions.** Read the template as it
> is today and work out which of its choices this user needs to confirm.
> Templates change, so the questions change with them.

**Templates:** `gorgias`; confirm with `bruin init --help`. Zendesk, Intercom,
Freshdesk and HubSpot have connectors but no template: read
`ingestion/<source>`; the modelling is theirs to build. CSAT in a survey tool:
`ingestion/satismeter`, `surveymonkey` or `typeform`.

**Watch for:**

- Raw copy only: no models, reports or checks; every metric definition is the user's.
- BigQuery only as shipped; another warehouse means changing each asset's destination.
- Current state only: an updated ticket overwrites its row, so past backlog and reopen counts need a snapshot asset.
- History loads slowly; estimate ticket and message volume before the first run.

**Usually needs the user's input:**

- Which tickets count: spam, trashed, merged, outbound, auto-closed, internal or test customers.
- First response: first public agent reply excluding auto-replies; clock start; business hours and timezone; per channel or not.
- Resolution: how reopened and snoozed tickets count.
- Contact reasons: tags, intents or custom fields, whichever the team maintains; check fill rate.
- CSAT: the scale, unanswered surveys, every closed ticket or a sample.
- The key joining a helpdesk customer to a paying customer, and its match rate.
- Whether message bodies may sit in the warehouse at all, and who can read them.

**Reconcile against:** the helpdesk's own statistics for tickets created and
average satisfaction over a settled recent week; compare response times only
once definitions match.

## Answer questions

Read [analysis.md](analysis.md).

## Never

- Ask for or print a credential; write, run, backfill, `--full-refresh` or
  touch production without a yes; put personal data in output.
- Write to the helpdesk: no replies, tags, merges, closes, deletes, macros or rules.
- Pull message bodies or survey comments into context; aggregate in SQL, and ask before sampling for themes.
- Rank or name individual agents unless the user asks for agent-level results.

## Unverified

- Daily runs may skip late CSAT scores; after a few runs, compare scored surveys per week with Gorgias.
- Gorgias's own metric definitions; read its statistics documentation before reconciling.
- Whether `mask` and `sql_exclude_columns` apply to Gorgias; load once into dev and inspect the columns.
