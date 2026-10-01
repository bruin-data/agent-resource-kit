---
name: pipeline-triage
description: Use when an alert fires, a scheduled tick runs, or someone asks what is broken right now in a Bruin pipeline. Pulls current state from Bruin Cloud, classifies every issue into exactly one class, and routes each class to the specialist skill that handles it. Read-only; it never repairs anything itself.
---

# Pipeline triage

**Status:** experimental · **Risk:** read-only

> **Upstream documentation wins.** Where this file disagrees with the
> [Bruin docs](https://getbruin.com/docs/bruin/overview.html) or `bruin --help`,
> upstream is right and this file is stale. Written against Bruin CLI
> `v0.11.765`, checked 2026-09-30.

This is the dispatcher. Every self-healing run starts here. Look at pipeline
state, decide what is wrong, hand each finding to a specialist. Do not repair
anything in this skill.

## Look it up live

This file says what to reach for and what to be careful about. For the facts
themselves, ask the tool, and tell the user if it disagrees with this file:

- **Flags:** `bruin <command> --help`. The docs lag the CLI.
- **Docs:** the local Bruin MCP server, `bruin_get_doc_content('<path>')`, or
  `https://getbruin.com/docs/bruin/<path>.html` without it. For this skill:
  `commands/cloud` for pipelines, runs, instances and validation errors,
  `cloud/mcp-setup` for the Cloud MCP tools, `commands/query` for warehouse
  probes, and `commands/ai-skills` for the built-in skills you route to.
- **The user's environment:** Bruin Cloud MCP, or
  `bruin cloud ... --output json`.

## Which skills you are routing to

Bruin's built-in diagnosis skills, installed with `bruin ai skills all`. Route
by the names the installed `SKILL.md` files carry, and read them rather than
restating what they do. The orchestration skills sit alongside them:
[`pipeline-backfill`](../pipeline-backfill/SKILL.md),
[`anomaly-investigate`](../anomaly-investigate/SKILL.md),
[`maintenance-pr`](../maintenance-pr/SKILL.md) and
[`pipeline-report`](../pipeline-report/SKILL.md).

## Access

Either Cloud interface works. Default to `bruin cloud ... --output json`; use
the Bruin Cloud MCP server when the host has it connected. Do not use local
`bruin run` for operational execution; it does not reflect Cloud state.

**Credentials.** Never ask for one in chat or pass one as a command argument.
For a source, the user runs `bruin connections add` with no flags (the
interactive prompt; its flag mode puts the secret on the command line) or
references `${VAR}` in `.bruin.yml`. For Cloud, `bruin cloud login` or an
exported `BRUIN_CLOUD_API_KEY`, never `--api-key`. `bruin auth status` shows
which is active without printing it.

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

Collect every signal below. Silence on one signal is itself a signal. Take the
exact commands and flags from `bruin cloud <command> --help`; the Cloud MCP
equivalents are named in brackets (some hosts add a `-tool` suffix).

1. **Project.** If more than one is visible and none was supplied, stop and
   ask. Do not guess.
2. **Pipeline inventory.** `bruin cloud pipelines list` and `pipelines get`
   (`pipeline-list`).
3. **Validation errors.** `bruin cloud pipelines errors`
   (`validation-error-list`). In `v0.11.765` it takes no project or pipeline
   filter, so filter the response client-side.
4. **Recent runs.** `bruin cloud runs list` over the `since` window
   (`pipeline-run-list`).
5. **Latest run and its diagnosis.** `bruin cloud runs get` and
   `runs diagnose`, with `--latest` or `--run-id`.
6. **Asset instances and failed logs.** `bruin cloud instances list` and
   `instances failed-logs`, scoped to the run with `--run-id <id>` or
   `--latest` (`asset-instance-list`, `asset-instance-logs`). `bruin cloud
   assets list` takes only a project and pipeline; it has no run scope.
7. **Asset health.** The Cloud MCP `asset-health` tool, where the host has it.
   Record "not checked" otherwise.
8. **Freshness.** Compare the last successful run and instance timestamps to
   the declared schedule or the historical cadence.
9. **Repository changes.** `git log`, recent branches and PRs touching the
   failing assets and their upstreams. Consider code before assigning cause.
10. **Warehouse probes, only if Cloud state is not enough.** Read-only
    `bruin query` with `--description "<why>"`, an explicit `--limit`, and a
    `--dry-run` first for expensive scans.

Read run and instance statuses from the response rather than from a fixed list;
the vocabulary differs between the CLI help, the docs and the MCP tools. Asset
instances may show `checks_failed`, which is not the same as `failed`.

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
