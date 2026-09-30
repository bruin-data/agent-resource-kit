---
name: pipeline-backfill
description: Use when a fix has merged, a transient failure needs a retry, or an upstream republished historical data, and a Bruin pipeline needs rerunning for a specific time range. Runs pre-flight checks on scope, materialisation and reversibility, then executes only through Bruin Cloud, one interval at a time, with approval gates.
---

# Pipeline backfill

**Status:** experimental · **Risk:** approval-required

> **Upstream documentation wins.** Where this file disagrees with the
> [Bruin docs](https://getbruin.com/docs/bruin/overview.html) or `bruin --help`,
> upstream is right and this file is stale. Written against Bruin CLI
> `v0.11.765`, checked 2026-09-29.

The most dangerous skill in the set. A backfill can overwrite good data,
double-count rows, or saturate a source connector. The guardrails matter more
than the speed.

## Access

Prefer the Bruin Cloud MCP server when it is connected. Otherwise use
`bruin cloud ... --output json`. Never substitute a local `bruin run`, or a
local `--full-refresh`, for a Cloud run; local execution does not reproduce
Cloud behaviour and leaves no auditable run record.

Never ask for a Bruin Cloud API key in chat, and never pass one as `--api-key`
on a command line where it lands in shell history and the process list. Tell
the user to run `bruin cloud login`, or to export `BRUIN_CLOUD_API_KEY`
themselves.

## When to use

- A code or schema fix merged and historical intervals need regenerating.
- A transient failure was diagnosed and the affected runs need retrying.
- An upstream source republished data for a past window.
- Someone asks to rerun a named pipeline over a named range.

Do not use for routine first runs, for a pipeline or asset that has never
succeeded (there is no "back" to fill), for source or raw table full refreshes,
for reruns whose consequences are not reversible, or for "just rerun
everything" with no scoped range.

## Inputs

| Input | Required | Example | Notes |
|---|---|---|---|
| `project_id` | no | `<your-project-id>` | Required when several projects are visible |
| `pipeline` | yes | `daily-orders` | Cloud pipeline name |
| `asset` | no | `marts.daily_revenue` | The asset that motivated the rerun. Drives risk analysis and verification |
| `start` / `end` | yes | `2026-05-01T00:00:00Z` | Use the pipeline's interval format. Do not assume inclusivity beyond Cloud's own run-window semantics |
| `reason` | yes | `schema fix for order_total` | Free text, logged with the run for audit |
| `mode` | no | `trigger` or `rerun` | Default `trigger`. Use `rerun` only against an existing run ID |
| `dry_run` | no | `true` | Default `true`. Set `false` only after the plan is approved |

## Pre-flight checks

Run every one before triggering anything. A single failure aborts the plan.

1. **Project and pipeline exist.** Confirm with `bruin cloud pipelines get`,
   and check `bruin cloud pipelines errors` for outstanding validation errors.
2. **Run history exists.** `bruin cloud runs list --limit 20`. Abort if the
   pipeline has never succeeded.
3. **Range is bounded.** More than 90 days needs explicit approval and usually
   smaller intervals.
4. **Range is in the past.** Backfilling future intervals is always a mistake.
5. **Intervals are meaningful.** Some assets do not use intervals, or use them
   wrongly. If slicing is not meaningful here, escalate rather than pretend it
   is safe.
6. **Materialisation strategy.** Classify the asset and its downstreams:
   `append`, `merge`, `delete+insert`, `time_interval`, `create+replace`,
   `truncate+insert`, `ddl`, `scd2_by_time`, `scd2_by_column`, and the data
   vault strategies. If you cannot estimate the consequence, escalate.
7. **Reversibility.** Identify where the data comes from and whether deleted
   rows can be restored. If restoration is impossible, uncertain or expensive,
   a human decides.
8. **Layer risk.** Classify the table as source or raw, intermediate, or final.
   Full refresh and any delete-style operation on a source or raw table is
   prohibited.
9. **Upstream coverage.** Every dependency needs successful runs covering the
   same interval. Missing intervals abort the plan, listed by name.
10. **Downstream awareness.** List downstream assets. If any is running, wait
    or abort.
11. **Size and cost.** Estimate volume and duration from run history and
    warehouse metadata. Large or expensive reruns need approval.
12. **Row count sanity.** Estimate output from one sample interval. More than
    ten times the historical volume aborts.
13. **Connector quotas.** If the source is rate limited or the destination
    quota limited, check current usage. Abort if the backfill would exhaust the
    day's budget.
14. **Confidence.** Below 90% confidence in the action or its consequences,
    stop and hand to a human.

## Commands

```bash
bruin cloud runs list    --project-id <id> --pipeline <p> --limit 20 --output json
bruin cloud runs get     --project-id <id> --pipeline <p> --latest  --output json
bruin cloud runs diagnose --project-id <id> --pipeline <p> --latest --output json

# Trigger an interval. --split batches the range into one run per unit,
# which is safer than one run over the whole range.
bruin cloud runs trigger --project-id <id> --pipeline <p> \
  --start-date <start> --end-date <end> --split day --output json

# Rerun an existing run, optionally only its failed assets.
bruin cloud runs rerun --project-id <id> --pipeline <p> \
  --run-id <run-id> --only-failed --output json
```

Trigger and rerun return a success envelope, not a run ID. Poll
`bruin cloud runs list --limit 1`, then verify the run you found with
`bruin cloud runs get --run-id <id>`. `bruin cloud backfills list` and
`backfills runs` inspect a split batch as one group.

Always set `--start-date` and `--end-date` explicitly. Check `bruin cloud runs
trigger --help` before using `--asset`, `--downstream`, `--full-refresh` or
`--chunk-size`; the flag set moves, and `--full-refresh` in particular is never
auto-allowed here.

## Guardrails

- **Allowed**: pre-flight checks, dry-run plan generation, and at most one
  small rerun where the pipeline already succeeded for the same interval shape,
  the target is not production or is explicitly pre-approved, and the action is
  reversible.
- **Requires approval**: ranges over 7 days, production pipelines, large or
  expensive tables, `append` reruns where data already exists, `merge` or
  `delete+insert` reruns with unclear keys or windows, any source with quota
  risk, and any rerun touching more than one interval.
- **Human only**: irreversible or ambiguous changes, confidence below 90%,
  unclear materialisation semantics, uncertain restore path, full refresh, and
  anything that risks destroying raw data.
- **Never**: future dates, a backfill with no `reason`, triggering while a run
  is in progress, skipping pre-flight, local operational runs, full refresh or
  delete-style operations on source and raw tables, or running the whole range
  as one trigger when meaningful smaller intervals exist.

When approval is required, emit the plan and stop. Do not poll for approval.
The caller resumes with `dry_run: false`.

## Verification

After each interval: the run status is `success`; the row count sits between
50% and 200% of the historical mean for the comparable day; checks and asset
instances passed; the run ID and URL are captured. If verification fails, stop.
Do not proceed to the next interval.

After the range: re-check the original failing condition, and list downstream
assets that may still need reruns. Never auto-cascade unless the approved plan
included them.

## Output

Write `.context/backfill-<asset>-<timestamp>.yml` and return the path. Record
the pipeline, range, reason, mode, materialisation strategy, layer, intervals
attempted and succeeded, run IDs and URLs, row counts before and after,
verification result, and downstream assets still blocked.

A backfill is not complete until the record is written. A partial backfill must
say so in plain words. Then call
[`pipeline-report`](../pipeline-report/SKILL.md).
