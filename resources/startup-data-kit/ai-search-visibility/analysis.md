# Answering search and AI visibility questions

> **Upstream documentation wins.** Where this file disagrees with the [Bruin
> docs](https://getbruin.com/docs/bruin/overview.html), `bruin --help`,
> Google's Search Console documentation, or a measurement tool's own
> documentation, those are right and this file is stale. Written against Bruin
> CLI `v0.11.766`, checked 2026-10-01.

Read `decisions.md` beside the pipeline's `pipeline.yml` first. The Never rules
in [SKILL.md](SKILL.md) apply.

## Before answering

- On `google-web-analytics`, read the report assets before writing SQL.
- Check freshness: the last runs (Bruin Cloud MCP or `bruin cloud runs list`), then the maximum date in the table.
- Name which of the three the question is about: Search Console is measured, crawler logs are observed, AI answers are sampled.
- Quote any AI visibility number with the tool, prompt set, assistants sampled and date range; without them it means nothing.

## Traps

- Search Console clicks will not match GA4 organic sessions; anonymised queries count in totals but not rows; never average average position; leave the last three days out.
- The template's value columns are modelled from key-event weights, not revenue.
- Brand mention and source citation are separate reads; prompt-set changes move the score, and branded prompts inflate it.
- Split crawlers into training, search-index and live user fetches (`GPTBot`, `OAI-SearchBot`, `ChatGPT-User`, `ClaudeBot`, `Claude-User`, `PerplexityBot`, `Google-Extended`, `Bytespider`, `Applebot-Extended`, `CCBot`); a live fetch is the nearest thing to a conversion signal.
- Check `robots.txt` before reading a crawler's absence as a signal.
- Push back on `llms.txt` as a ranking lever, keyword density, word-count targets, mass-generated content, or any fixed technique that "gets you into ChatGPT".

## What this data cannot tell you

- Whether "we are in ChatGPT": only a sampled prompt set on a stated date; there is no ground truth.
- Why rankings dropped, until algorithm updates and the deploy log are checked.
- Revenue from SEO, without a landing-page-to-signup key; organic stops at clicks.
- What to write next, beyond impressions without clicks as a proxy.
