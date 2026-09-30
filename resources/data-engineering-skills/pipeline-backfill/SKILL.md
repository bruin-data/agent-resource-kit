---
name: pipeline-backfill
description: Use when a fix has merged, a transient failure needs a retry, or an upstream republished historical data, and a Bruin pipeline needs rerunning for a specific time range. Runs pre-flight checks on scope, materialisation and reversibility, then executes only through Bruin Cloud, one interval at a time, with approval gates.
---

# Pipeline backfill

**Status:** experimental · **Risk:** approval-required

> **Upstream documentation wins.** Where this file disagrees with the
> [Bruin docs](https://getbruin.com/docs/bruin/overview.html) or `bruin --help`,
> upstream is right and this file is stale. Written against Bruin CLI
> `v0.11.765`, checked 2026-09-30.

The most dangerous skill in the set. A backfill can overwrite good data,
double-count rows, or saturate a source connector. The guardrails matter more
than the speed.

## Look it up live

This file says what to reach for and what to be careful about. For the facts
themselves, ask the tool, and tell the user if it disagrees with this file:

- **Flags:** `bruin <command> --help`. The docs lag the CLI. For this skill,
  `bruin cloud runs trigger --help` before every trigger.
- **Docs:** the local Bruin MCP server, `bruin_get_doc_content('<path>')`, or
  `https://getbruin.com/docs/bruin/<path>.html` without it. For this skill:
  `commands/cloud` for runs, reruns and backfills, `cloud/backfills` for Cloud
  backfill limits and behaviour, `assets/materialization` for what each strategy
  does to existing rows, `assets/interval-modifiers` for shifted windows, and
  `commands/backfill` for how the local command differs.
- **The user's environment:** Bruin Cloud MCP, or
  `bruin cloud ... --output json`.

## Access

Either Cloud interface works. Default to `bruin cloud ... --output json`; use
the Bruin Cloud MCP server when the host has it connected. Never substitute a
local `bruin run`, a local `bruin backfill`, or a local `--full-refresh`, for a
Cloud run; local execution does not reproduce Cloud behaviour and leaves no
auditable run record.

**Credentials.** Never ask for one in chat or pass one as a command argument.
For a source, the user runs `bruin connections add` with no flags (the
interactive prompt; its flag mode puts the secret on the command line) or
references `${VAR}` in `.bruin.yml`. For Cloud, `bruin cloud login` or an
exported `BRUIN_CLOUD_API_KEY`, never `--api-key`. `bruin auth status` shows
which is active without printing it.

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
| `start` / `end` | yes | `2026-05-01T00:00:00Z` | Use the pipeline's interval format. With `--split`, `--end-date` is exclusive, so pass one period past the last one you want. See `commands/cloud` |
| `reason` | yes | `schema fix for order_total` | Free text. Pass it as `--note` on the trigger, which shows in the Cloud activity log |
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
6. **Materialisation strategy.** Read the strategy of the asset and each
   downstream, and classify what it does to rows already in the window: keeps
   them and adds more, replaces them, or rebuilds the whole table.
   `assets/materialization` is the list of strategies and what each does. If
   you cannot estimate the consequence, escalate.
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

Take the commands and flags from `commands/cloud` (runs, backfills) and
`bruin cloud runs trigger --help`, not from memory. Three things are fixed here
whatever the flag set says:

- Always pass `--split`, so the range runs as one child run per interval
  rather than one run over the whole range.
- Always set `--start-date` and `--end-date` explicitly. With `--split`, the
  end is exclusive, `[start, end)`. The local `bruin backfill` treats a
  date-only end as inclusive and a timestamp end as exclusive
  (`commands/backfill`), so do not carry its dates into a Cloud trigger.
- Always pass `--note <reason>`.

Check `--help` before using `--asset`, `--downstream`, `--full-refresh` or
`--chunk-size`; the flag set moves, and `--full-refresh` in particular is never
auto-allowed here. `--tag` labels the run in the activity log. It does not
select assets; `--asset` does.

Finding the run you started:

- A plain trigger prints the created run ID; with `--output json` it is in
  `run_id`. Verify it with `bruin cloud runs get --run-id <id>`.
- A `--split` trigger prints a backfill ID and a tracking URL instead, because
  the child runs are created asynchronously. Inspect the batch with
  `bruin cloud backfills list` and `backfills runs --id <backfill-id>`.
- For `runs rerun`, confirm the resulting run with `bruin cloud runs list` and
  `runs get` before you verify anything. See Unverified below.

What Cloud does that a plan must account for, per `cloud/backfills`:

- A backfill holds at most 250 child runs. Plan larger ranges as several
  batches, or a coarser split.
- Interval modifiers are always applied to every child run in Cloud, with no
  toggle, so child windows can overlap. Check the asset for `interval_modifiers`
  before assuming each run touches only its own interval.
- Cross-pipeline sensors still apply. A child run waits for its external
  upstream interval to complete, so pre-flight 9 covers upstreams in other
  pipelines too.

The Cloud MCP `backfill-trigger` tool accepts per-asset `asset_overrides`, and
its own schema documents `FULL_REFRESH` there as forcing a full refresh. The
full-refresh rules in this skill cover that path exactly as they cover
`--full-refresh`.

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

## Unverified

**What `bruin cloud runs rerun` prints.** `commands/cloud` documents the
trigger output but not the rerun output, and checking it needs a live rerun,
which was not run for this file. Until you have seen it, find the new
run with `bruin cloud runs list --pipeline <p> --limit 5 --output json` and
confirm it with `runs get --run-id <id>` before verifying the interval.
