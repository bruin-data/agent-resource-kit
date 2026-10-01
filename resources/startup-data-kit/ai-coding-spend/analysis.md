# Answering AI coding spend questions

> **Upstream documentation wins.** Where this file disagrees with the [Bruin
> docs](https://getbruin.com/docs/bruin/overview.html), `bruin --help`, or
> Anthropic's or Cursor's API documentation, those are right and this file is
> stale. Written against Bruin CLI `v0.11.766`, checked 2026-10-01.

Read `decisions.md` beside the pipeline's `pipeline.yml` first. The Never rules
in [SKILL.md](SKILL.md) apply.

## Before answering

- Read the mart assets before writing SQL, and query the marts; raw and staging may hold only the last run's window.
- Check freshness: the last runs (Bruin Cloud MCP or `bruin cloud runs list`), then gaps per platform; one vendor missing days reads as a usage drop or a tool shift.
- State the definition, exact UTC window, coverage and what cost includes with every number.

## Traps

- Estimated cost is consumption at the vendor's rate, not spend; say which vendor dominates a total.
- When cost moves, check tokens and model mix first; cache reads inflate token totals cheaply.
- `sessions`, `requests` and `lines_added` are different measures per platform; compare platforms on tokens, active users and active days.
- Anthropic rows using several models arrive combined as a model set; do not split them, show their share.
- API-key actors are not people but count as active users; separate them, and check email overlap before counting cross-platform users.
- Adoption needs a denominator (seats or headcount) from outside the pipeline, and "active" needs the user's definition.

## What this data cannot tell you

- Productivity, quality or value; lines, tokens and commits measure activity.
- Who is a good engineer; heavy and light use each have good and bad explanations.
- ROI, without an outcome measure from elsewhere, and then only as a correlation.
- Use outside the covered channels.
