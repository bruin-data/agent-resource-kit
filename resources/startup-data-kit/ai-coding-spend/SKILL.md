---
name: ai-coding-spend
description: Use when a startup wants AI coding tool usage and spend set up or answered. Sets up the ai-coding-usage template (Claude Code and Cursor into DuckDB) and answers adoption, active user, token, estimated cost and model mix questions by team.
---

# AI coding spend

**Status:** experimental · **Risk:** approval-required

> **Upstream documentation wins.** Where this file disagrees with the [Bruin
> docs](https://getbruin.com/docs/bruin/overview.html), `bruin --help`, or
> Anthropic's or Cursor's API documentation, those are right and this file is
> stale. Written against Bruin CLI `v0.11.766`, checked 2026-10-01.

Sets up a Claude Code and Cursor usage pipeline and answers adoption and cost
questions from it. It exists to prevent an estimated cost being read as the
bill, and usage data being turned into a ranking of engineers.

## Set up

Follow [workflow.md](workflow.md).

> **Important: do not ask a fixed list of questions.** Read the template as it
> is today and work out which of its choices this user needs to confirm.
> Templates change, so the questions change with them.

**Templates:** `ai-coding-usage`; confirm with `bruin init --help`. Not on
DuckDB: read `ingestion/anthropic` and `ingestion/cursor`; the modelling is
theirs to build.

**Watch for:**

- Coverage is Claude Code on the first-party Anthropic API, and Cursor; Bedrock, Vertex AI, Foundry, Claude Platform on AWS, Claude Enterprise claude.ai users and every other tool are silently missing.
- Cost columns are estimates, not the bill, built differently per vendor, with no seat fees; no seat list is ingested.
- History lives only in the marts; `--full-refresh` drops it.

**Usually needs the user's input:**

- What "cost" should mean: spend, consumption, or both.
- Billing model: seats, pay-as-you-go or mixed, and whether to carry it into the marts.
- Identity: the cross-platform join is lowercased email; aliases, contractors, second accounts.
- Teams: neither source has one; a mapping from email to team, and where it lives.
- Seats: utilisation needs a seat or member list added.
- Users to exclude: test accounts, shared or CI keys, departed staff.
- How far back history matters.

**Reconcile against:** each vendor's own usage page for one settled UTC day;
tokens and active users should match, cost only once "cost" is defined.

## Answer questions

Read [analysis.md](analysis.md).

## Never

- Ask for or print a credential; write, run, backfill, `--full-refresh` or
  touch production without a yes; put personal data in output.
- Rank, score or judge individual engineers from usage; report at team or organisation level.
- Call estimated cost "spend" or "the bill" without saying what it includes.
- Write to Anthropic or Cursor, or use an admin key outside the pipeline's ingestion.

## Unverified

- Whether rerunning a day duplicates Claude Code rows; after a rerun, check `raw.claude_code_usage` for repeated keys.
- How Anthropic computes `estimated_cost`, and whether it is filled for subscription usage; compare one day with the Console.
- Whether a read-only Cursor key covers the analytics endpoints; with approval, try one on a one-day run.
