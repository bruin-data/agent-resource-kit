# Answering support analytics questions

> **Upstream documentation wins.** Where this file disagrees with the [Bruin
> docs](https://getbruin.com/docs/bruin/overview.html), `bruin --help`, or
> Gorgias, Zendesk, Intercom, Freshdesk or HubSpot documentation, those are
> right and this file is stale. Written against Bruin CLI `v0.11.766`, checked
> 2026-10-01.

Read `decisions.md` beside the pipeline's `pipeline.yml` first. The Never rules
in [SKILL.md](SKILL.md) apply.

## Before answering

- Read any models the user built before writing SQL; the template ships raw tables only. Do not infer meaning from timestamp column names.
- Check freshness: the last runs (Bruin Cloud MCP or `bruin cloud runs list`), then the latest update time per raw table; a missing load reads as a quiet week.
- State source, window and definition (clock start and stop, business hours or wall clock) with every number.
- Apply the agreed ticket population and state the exclusions; if none were agreed, say the number is unfiltered.

## Traps

- A first response of seconds is a rule, not an agent; use the median and a high percentile, split by channel.
- Open tickets have no resolution time and tickets with no agent reply are not zero; report both counts, or recent weeks look faster.
- Only the latest close is kept, so a reopened ticket looks like one long resolution.
- Tickets carry several tags, so shares sum past 100% unless you pick a primary reason; a new tag reads as a new problem.
- Report CSAT with its response rate and count; respondents skew to extremes and the latest week is incomplete.
- On a revenue join, report the match rate and normalise per customer or order; larger customers raise more tickets.

## What this data cannot tell you

- Backlog on a past date, unless snapshots exist.
- Why customers did not write in; silence is not satisfaction.
- Whether a fix worked, from volume alone; volume moves with traffic, orders, releases and seasons.
- Agent quality from speed, or cause from tickets rising before churn; report the relationship and sample size.
