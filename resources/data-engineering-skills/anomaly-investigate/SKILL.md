---
name: anomaly-investigate
description: Use when a tracked metric spikes or dips but no pipeline error and no quality check fired, or when someone asks why a number moved on a particular day. Slices the metric by dimension, checks upstream row counts and distributions, and produces an attribution backed by evidence. Read-only; it never corrects the data.
---

# Anomaly investigate

**Status:** experimental · **Risk:** read-only

> **Upstream documentation wins.** Where this file disagrees with the
> [Bruin docs](https://getbruin.com/docs/bruin/overview.html) or `bruin --help`,
> upstream is right and this file is stale. Written against Bruin CLI
> `v0.11.765`, checked 2026-09-30.

The asset ran. The checks passed. The number still looks wrong. This skill
finds out why by attribution, not by guesswork.

## Look it up live

This file says what to reach for and what to be careful about. For the facts
themselves, ask the tool, and tell the user if it disagrees with this file:

- **Flags:** `bruin <command> --help`. The docs lag the CLI. For this skill,
  `bruin query --help` and `bruin lineage --help`.
- **Docs:** the local Bruin MCP server, `bruin_get_doc_content('<path>')`, or
  `https://getbruin.com/docs/bruin/<path>.html` without it. For this skill:
  `commands/query` for warehouse queries, `commands/lineage` for upstreams and
  downstreams, and `commands/cloud` for runs and instances.
- **The user's environment:** Bruin Cloud MCP, or
  `bruin cloud ... --output json`.

## Access

Use `bruin cloud ... --output json`, or the Bruin Cloud MCP server when the host
has it, for run and asset context. Local repository inspection is allowed for
metric definitions, lineage and git history. Local operational runs are not.

**Credentials.** Never ask for one in chat or pass one as a command argument.
For a source, the user runs `bruin connections add` with no flags (the
interactive prompt; its flag mode puts the secret on the command line) or
references `${VAR}` in `.bruin.yml`. For Cloud, `bruin cloud login` or an
exported `BRUIN_CLOUD_API_KEY`, never `--api-key`. `bruin auth status` shows
which is active without printing it.

## When to use

- A monitored metric sits well outside its expected range.
- Someone asks why a number spiked or dropped on a given date.
- [`pipeline-triage`](../pipeline-triage/SKILL.md) classified an issue as
  `anomaly`.
- A dashboard consumer reported that a number looks off.

Do not use for failed runs, which go to `pipeline-diagnose`; schema problems,
which go to `schema-drift-check`; missing data, which goes to
`freshness-check`; duplicated rows, which go to `duplicate-investigate`; or
proving that a real-world business event happened. Those four skills ship with
the CLI and install with `bruin ai skills all`.

## Inputs

| Input | Required | Example | Notes |
|---|---|---|---|
| `metric` | yes | `marts.daily_revenue.total_revenue` | Metric, or asset and column |
| `window` | yes | `2026-05-21` | A date or a range |
| `project_id` | no | `<your-project-id>` | For Cloud run and asset context |
| `pipeline` | no | `daily-orders` | Inferred from the metric's asset where possible |
| `dimensions` | no | `[country, source, category]` | Inferred from the asset's columns otherwise |
| `baseline` | no | `last_28d_same_dow` | Default: same day of week over four weeks, median |

## Context to gather

1. **Metric history.** At least 28 days of daily values plus the window in
   question, through `bruin query`.
2. **Baseline.** Median and interquartile range over the baseline window, using
   the same day of week where seasonality matters.
3. **Magnitude.** How many IQRs or sigmas off, *and* the absolute delta. Both
   matter: a large percentage on a tiny base is noise.
4. **Dimension breakdowns.** The metric sliced by each candidate dimension,
   window against baseline. Find where the anomaly concentrates.
5. **Cloud context.** The runs, their diagnosis and the asset instances for
   that window. "Checks passed" means the run status is `success` and the asset
   instance is neither `failed` nor `checks_failed`, depending on which
   response you are reading.
6. **Upstream row counts.** Did the source row count move on that date?
7. **Upstream distributions.** Did a column's distribution shift even though
   the row count held steady?
8. **Code changes.** `git log` and recent PRs on the metric's asset and its
   upstreams over the last 30 days.
9. **Lineage.** `bruin lineage` on the metric's asset, with the full upstream
   and downstream set and the variant where the pipeline uses variants.
10. **External calendar.** Holidays, launches, maintenance windows, paid
    acquisition pulses. If no calendar is available, record this as
    "not checked" rather than omitting it.

Every warehouse query is read-only and carries a `--description` for the audit
trail. Always pass `--limit`: its default is 0, which returns every row. Run
`--dry-run` first on wide scans. Never pass `--dangerously-bypass-soft-limits`
without explicit approval.

## Attribution patterns

| Pattern | Signal | What it means |
|---|---|---|
| `single-dimension-driver` | One dimension value accounts for over half the delta | That segment moved. Report it |
| `pipeline-double-count` | Upstream row count is normal but the metric is a multiple | A pipeline defect. Route to `duplicate-investigate` |
| `pipeline-undercount` | Upstream rows dropped with no logged source failure | The interval is incomplete. Route to `freshness-check` |
| `new-segment` | The delta comes entirely from a value absent from the baseline | Something launched. Confirm against the calendar |
| `lost-segment` | A previously present value disappeared | Source dropped it, or collection stopped. Escalate |
| `seasonality-not-modelled` | The date recurs (month end, payday, holiday) and prior occurrences show the same shape | The baseline is wrong, not the data |
| `definitional-change` | A recent commit changed how the metric is computed | The number is right under the new definition. Surface the commit |
| `upstream-distribution-shift` | Row count steady, distribution moved | Often a real business change. Report without claiming cause |
| `unexplained` | Nothing above attributes more than half the delta | Say so, with the full breakdown |

## Method

Pull the history, compute the baseline, measure the observed value. If the
magnitude is within noise on both the relative and the absolute test, stop and
return `within-noise`; a small move is not an anomaly just because someone
asked about it.

Otherwise slice by every candidate dimension, pull upstream row counts and
distributions, read the last 30 days of commits on the metric's lineage, and
attribute the delta. Coverage above 50% is `anomaly-explained`. Below that it
is `anomaly-unexplained`, and it must be reported that way.

## Guardrails

- **Allowed**: reading metric and asset data, inspecting Cloud state, running
  capped read-only slicing queries, reading git and PR history, writing the
  report to `.context/`.
- **Requires approval**: nothing. This skill is read-only.
- **Never**: local operational runs; claiming a cause with no evidence link;
  "correcting" anomalous data; suppressing the anomaly from a dashboard or an
  alert; attributing more than 100% of the delta, which is the usual failure
  when overlapping dimensions get double-counted.

## Verification

This skill's output is verified by what happens next. If a pipeline cause was
attributed, the follow-up fix should return the metric to baseline; if it does
not, the attribution was wrong. If a real-world cause was attributed, no fix is
expected, the metric holds at its new level, and the baseline needs updating.
Record the outcome on the report so attribution accuracy can be tracked over
time.

## Output

Write `.context/anomaly-<metric>-<window>-<timestamp>.yml` and return the path.

```yaml
metric: marts.daily_revenue.total_revenue
window: 2026-05-21
magnitude:
  observed: 4_812_000
  baseline_median: 2_140_000
  abs_z_score: 4.8
  delta_pct: +124.9
primary_drivers:
  - dimension: country
    value: <country-code>
    contribution_pct: 78
coverage_pct: 92
unexplained_pct: 8
recent_commits_examined: 6
recent_commits_relevant: 0
attribution: single-dimension-driver + upstream-distribution-shift
recommended_next:
  action: human-review
  note: Concentrated in one country. No pipeline action recommended.
```

A report with coverage below 50% is unexplained. Say so. Do not stretch the
attribution to make the report look finished. Then call
[`pipeline-report`](../pipeline-report/SKILL.md).
