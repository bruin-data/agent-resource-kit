# Answering marketing questions

> **Upstream documentation wins.** Where this file disagrees with the [Bruin
> docs](https://getbruin.com/docs/bruin/overview.html), `bruin --help`, or an ad
> platform's documentation, those are right and this file is stale. Written
> against Bruin CLI `v0.11.766`, checked 2026-10-01.

Read `decisions.md` beside the pipeline's `pipeline.yml` first. The Never rules
in [SKILL.md](SKILL.md) apply.

## Before answering

- Read the report and model assets before writing SQL; channel mapping and joins live there, not in column names.
- Check freshness per platform: the last runs (Bruin Cloud MCP or `bruin cloud runs list`), then the maximum date in each raw ad table; one platform failing to load reads as that channel's spend dropping.
- State source, window, attribution model, currency and cost basis with every number.
- CAC, ROAS and payback need spend joined to billing; if that identity join does not exist, say so rather than answering from one side.

## Traps

- Never add conversions across platforms; each claims credit for the same one.
- Attribution windows differ per platform, view-through inflates platform numbers, and iOS ATT and cookie loss degraded platform attribution.
- A daily join across two timezones is off by a partial day, every day.
- The average of daily rates is not the rate: sum numerators and denominators, and report the denominator.
- Recent days undercount while conversions land, and months differ in length; label incomplete or unequal windows.
- A renamed campaign looks like one ending and another starting; join on ID, not name.

## What this data cannot tell you

- Which channel caused growth: that needs an experiment or holdout.
- Whether to cut a channel: that needs incrementality, not attributed ROAS.
- Why CPMs rose: usually auction dynamics you cannot see; say so.
- True CAC: which costs count (paid only, salaries, tooling) is a decision; ask.
