---
name: pipeline-triage
description: Use when an alert fires, a scheduled tick runs, or someone asks what is broken right now in a Bruin pipeline. Pulls current state from Bruin Cloud, classifies every issue into exactly one class, and routes each class to the specialist skill that handles it. Read-only; it never repairs anything itself.
---

# Pipeline triage

**Status:** experimental · **Risk:** read-only

> **Upstream documentation wins.** Where this file disagrees with the
> [Bruin docs](https://getbruin.com/docs/bruin/overview.html) or `bruin --help`,
> upstream is right and this file is stale. Written against Bruin CLI
> `v0.11.765`, checked 2026-09-29.

This is the dispatcher. Every self-healing run starts here. Look at pipeline
state, decide what is wrong, hand each finding to a specialist. Do not repair
anything in this skill.

## Which skills you are routing to

Bruin's CLI ships the diagnostic skills. Install them once, then route by name:

```bash
bruin ai skills all
```

That installs `pipeline-diagnose`, `schema-drift-check`,
`quality-check-investigate`, `freshness-check`, `duplicate-investigate`,
`maintenance-action` and `bruin-semantic-layer`. Do not restate what they do;
read the installed `SKILL.md`. The orchestration skills sit alongside them:
[`pipeline-backfill`](../pipeline-backfill/SKILL.md),
[`anomaly-investigate`](../anomaly-investigate/SKILL.md),
[`maintenance-pr`](../maintenance-pr/SKILL.md) and
[`pipeline-report`](../pipeline-report/SKILL.md).

## Access

Prefer the Bruin Cloud MCP server when it is connected. Otherwise use
`bruin cloud ... --output json`. Do not use local `bruin run` for operational
execution; it does not reflect Cloud state.

Never ask for a Bruin Cloud API key in chat, and never pass one as `--api-key`
on a command line where it lands in shell history and the process list. Tell
the user to run `bruin cloud login`, or to export `BRUIN_CLOUD_API_KEY`
themselves. Warehouse credentials go through `bruin connections add`.

## When to use

- An alert fired and woke an agent.
- A scheduled tick runs and there is no specific alert.
- Someone asks "what is broken", "what needs attention", "is this healthy".
- Another skill needs a fresh state snapshot before acting.

Do not use for a targeted single-asset deep dive; that is `pipeline-diagnose`.
Do not use it to run fixes.

## Inputs

| Input | Required | Example | Notes |
|---|---|---|---|
| `pipeline` | yes | `daily-orders` | Pipeline name, or `all` to scan everything visible |
| `project_id` | no | `<your-project-id>` | Resolve via MCP or `bruin cloud projects list`; ask if several are visible |
| `since` | no | `24h` | Lookback for failed runs. Default `24h` |
| `severity_floor` | no | `warn` | Ignore anything below. Default `warn` |

## Context to gather

Run all of these. Silence on one signal is itself a signal.

1. Resolve the project. If more than one is visible and none was supplied,
   stop and ask. Do not guess.
2. Pipeline inventory: `bruin cloud pipelines list --project-id <id>
   --output json`, and `pipelines get --name <pipeline>` for one pipeline.
3. Validation errors: `bruin cloud pipelines errors --output json`. Filter by
   project and pipeline client-side; check `--help` before assuming a flag.
4. Recent runs: `bruin cloud runs list --project-id <id> --pipeline <p>
   --limit 20 --output json`.
5. Latest run and its diagnosis: `bruin cloud runs get ... --latest` and
   `bruin cloud runs diagnose ... --latest`, both `--output json`.
6. Asset and instance state: `bruin cloud assets list`, `bruin cloud instances
   list` and `bruin cloud instances failed-logs`, each scoped to the run with
   `--run-id <id>` or `--latest`.
7. Freshness: compare the last successful run and instance timestamps to the
   declared schedule or the historical cadence.
8. Repository changes: `git log`, recent branches and PRs touching the failing
   assets and their upstreams. Consider code before assigning cause.
9. Warehouse probes only if Cloud state is not enough. Use read-only
   `bruin query --connection <c> --query <sql> --description "<why>"
   --limit 1000 --output json`, and dry-run expensive scans first.

Treat run statuses as the API returns them: `success`, `failed`, `running`.
Asset instances may also show `checks_failed`.

Cache the raw output in `.context/triage-<timestamp>.json` so downstream skills
read it rather than re-querying.

## Classification

Every issue gets exactly one primary class. Take the first that matches.

| Class | Signal | Route to |
|---|---|---|
| `transient` | One failed run, error matches a retry pattern (timeout, 5xx, deadlock, connection reset), no recent code change | `pipeline-backfill`, retry once |
| `source-down` | Several assets sharing one upstream connector fail with auth or connectivity errors | Human. Do not retry until the source is verified |
| `schema-drift` | Unknown column, type mismatch, missing field, or validation flags drift | `schema-drift-check` |
| `quality-fail` | Run status `success` but a custom or column check failed | `quality-check-investigate` |
| `duplicate` | Uniqueness check failed, or row counts show repeated ingestion | `duplicate-investigate` |
| `stale` | Nothing failed but the data is past its freshness expectation | `freshness-check` |
| `anomaly` | Run succeeded, no instance is `failed` or `checks_failed`, but a tracked metric is out of range | `anomaly-investigate` |
| `code-regression` | Failure started immediately after a commit touching the failing asset | Human, with a link to the commit. Never auto-revert |
| `capacity` | OOM, quota exceeded, slot exhaustion, or a timeout on a query that historically ran fine | Human. Capacity changes need approval |
| `unknown` | Nothing above matches | `pipeline-diagnose`, to gather more |

Group issues by class before handing off, so a specialist sees one batch of
similar problems rather than a mixed bag. Hand off once per class, not once per
asset.

## Guardrails

- **Allowed**: reading Cloud state, reading repository and git history, writing
  the snapshot to `.context/`, invoking other skills.
- **Never**: local operational runs; skipping classification, because every
  issue gets a class even if that class is `unknown`; batching unrelated
  classes into one specialist call; reporting health from partial data.

If Bruin Cloud is unreachable, write `.context/triage-error-<timestamp>.yml`
and stop. Missing data is not the same as no failures, and must never be
reported as such.

## Verification

Re-read the snapshot five minutes after the last specialist finishes. Any class
that did not move to `resolved` or `escalated` is a routing failure. Log it and
reclassify rather than closing the run.

## Output

Write `.context/triage-summary-<timestamp>.yml` and return the path.

```yaml
pipeline: daily-orders
window: 24h
snapshot: .context/triage-20260522T1430Z.json
issues:
  - class: schema-drift
    severity: error
    assets: [raw.orders]
    routed_to: schema-drift-check
  - class: stale
    severity: warn
    assets: [marts.daily_revenue]
    routed_to: freshness-check
healthy_assets: 42
```

Finish the run by calling [`pipeline-report`](../pipeline-report/SKILL.md),
even when nothing was wrong. A silent run is indistinguishable from an agent
that never ran.
