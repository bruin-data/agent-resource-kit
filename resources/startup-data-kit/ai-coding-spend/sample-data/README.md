# Sample data for ai-coding-spend

> **Upstream documentation wins.** Where this file disagrees with the
> [`ai-coding-usage` template README](https://getbruin.com/docs/bruin/getting-started/templates-docs/ai-coding-usage-README.html),
> the [seed asset docs](https://getbruin.com/docs/bruin/assets/seed.html) or
> `bruin run --help`, those are right and this file is stale. Written against
> Bruin CLI `v0.11.767`, checked 2026-10-02.

**Every value here is invented.** Seven fictional people on `example.com`, one
CI key, two fictional weeks (2026-09-14 to 2026-09-27), made-up model names
and made-up per-token rates. Nothing is taken from real usage or real pricing.
[`generate.py`](generate.py) rebuilds the CSVs from a fixed seed.

It runs the real `ai-coding-usage` template with no Anthropic or Cursor key and
no warehouse: three seed assets take the place of the three API ingestion
assets, and everything downstream is the template, unchanged.

| File | Replaces | Shape |
|---|---|---|
| `claude_code_usage.asset.yml` + `.csv` | `raw.claude_code_usage` | One row per actor, day and terminal |
| `cursor_daily_usage.asset.yml` + `.csv` | `raw.cursor_daily_usage` | One row per person and day, active or not |
| `cursor_usage_events.asset.yml` + `.csv` | `raw.cursor_usage_events` | One row per request, `tokenUsage` as JSON |

## Try it

Needs the [Bruin CLI](https://getbruin.com/docs/bruin/getting-started/introduction/installation.html)
and git. Run it in an empty folder that is not inside a git repository.

```bash
# 1. Get the template and the sample data
git clone --depth 1 https://github.com/bruin-data/agent-resource-kit
bruin init ai-coding-usage ai-coding-demo

# 2. Swap the Anthropic and Cursor API assets for the fake CSVs
cp agent-resource-kit/resources/startup-data-kit/ai-coding-spend/sample-data/*.{asset.yml,csv} \
   bruin/ai-coding-demo/assets/raw/

# 3. Build every table on DuckDB, then query one
cd bruin
bruin run ai-coding-demo --full-refresh --workers 1 --start-date 2026-09-14 --end-date 2026-09-27
bruin query -c duckdb-default -q "SELECT strftime(date_trunc('week', usage_date), '%Y-%m-%d') AS week, platform, CAST(SUM(total_tokens) AS BIGINT) AS tokens, ROUND(SUM(estimated_cost_usd), 2) AS est_cost_usd FROM marts.ai_coding_usage_by_user_day GROUP BY ALL ORDER BY ALL"
```

Then install the skill and ask your agent something the data can answer, such
as "why did estimated Claude Code cost rise in the second week?" The data has a
definite answer to that question, and two details that can lead an agent to a
wrong one.

What the flags do:

- `--full-refresh`: the template's per-day marts use the `time_interval`
  strategy, which needs the table to exist, and Bruin's
  [materialization docs](https://getbruin.com/docs/bruin/assets/materialization.html)
  say to create it on the first run this way. It drops and rebuilds every table
  in the pipeline. That is harmless on this new demo database and destroys
  history on a real one, so never carry it into a real pipeline's later runs.
- `--workers 1`: with the default workers, two of five test runs failed on the
  DuckDB file lock, when a seed load and another asset or check opened the file
  at the same moment.
- The dates: by default `bruin run` covers yesterday, which has no sample rows.

Outside a git repository `bruin init` creates a `bruin/` project folder holding
`.bruin.yml` and the pipeline; inside one it puts the pipeline at the
repository root instead, so adjust the paths. The template still adds Anthropic
and Cursor connections to `.bruin.yml` as `${...}` references; with the API
assets swapped out, nothing reads them.

## Unverified

- **`schema_naming: direct`** on the two Cursor seed assets keeps the camelCase
  column names the template's staging SQL expects. Without it the seed loader
  converted them to snake_case and staging failed. The parameter is not in the
  seed asset docs; it was observed working on `v0.11.767`. If staging fails on
  a column such as `isActive`, check `bruin run --help` and the seed docs for
  the current option.
- **The first-run failure** without `--full-refresh` was observed on
  `v0.11.767`. The template's own README shows a plain `bruin run .`. Run
  without the flag first on a newer CLI to see whether it is still needed.
