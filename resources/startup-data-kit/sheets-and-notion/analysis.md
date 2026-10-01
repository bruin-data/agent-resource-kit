# Answering sheets and Notion questions

> **Upstream documentation wins.** Where this file disagrees with the [Bruin
> docs](https://getbruin.com/docs/bruin/overview.html), `bruin --help`, or
> Google Sheets or Notion documentation, those are right and this file is
> stale. Written against Bruin CLI `v0.11.766`, checked 2026-10-01.

Read `decisions.md` beside the pipeline's `pipeline.yml` first. The Never rules
in [SKILL.md](SKILL.md) apply.

## Before answering

- Read the staging models before writing SQL and prefer them; raw is the file as typed, totals rows included.
- Check freshness: the last runs (Bruin Cloud MCP or `bruin cloud runs list`); the warehouse holds the file as of the last run, so "I just updated the sheet" is stale until the next.
- Check the raw columns still match what staging expects; a renamed header is the commonest overnight change.
- State the file, tab or database, and the run date, with every number.

## Traps

- A target is a plan: say whose and which version; without history it may be today's re-forecast, hiding the miss against the original.
- A mapping is someone's judgement; say when it was last reviewed, if anyone knows.
- A key duplicated on the sheet side multiplies totals; compare totals before and after the join.
- Report the match rate both ways and keep unmatched rows as `unmapped`; a join on names is approximate.
- Targets and actuals must share grain, calendar, currency and definition; the current month is partial, not a miss.
- On Notion, the user sees a filtered view while the load is the whole database, and "Done" is a convention, not an event.

## What this data cannot tell you

- Who changed a value, when or why; edit history is not loaded.
- Whether a plan was ever agreed; a number in a sheet may be a draft.
- Anything the file never held; a missing row and a zero look the same after a join.
