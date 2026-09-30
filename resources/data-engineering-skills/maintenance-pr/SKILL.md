---
name: maintenance-pr
description: Use when a diagnostic skill has produced a finding that calls for a routine repository change to a Bruin pipeline, such as a column rename, a type widening, a removed-column cleanup, a description update, a check threshold change or a dependency bump. Opens one draft pull request, gated on an allow-list and never opened unprompted.
---

# Maintenance PR

**Status:** experimental · **Risk:** approval-required

> **Upstream documentation wins.** Where this file disagrees with the
> [Bruin docs](https://getbruin.com/docs/bruin/overview.html) or `bruin --help`,
> upstream is right and this file is stale. Written against Bruin CLI
> `v0.11.765`, checked 2026-09-30.

The only skill in the set with write access to the repository. Every PR it
opens must trace back to a finding file. No freelancing.

Bruin's built-in diagnosis skills return a text diagnosis and write no file.
When one of them produced the finding, the orchestrating agent writes the
finding file into `.context/` from that returned diagnosis, quoting its
evidence, before calling this skill. Other skills in this catalogue write their
own.

Bruin's own `maintenance-action` skill, installed with `bruin ai skills all`,
defines what a controlled action is and asks for approval policy. This skill is
the narrower case: turning a finding into a reviewable pull request, with an
allow-list of change types that decides what may proceed without a human. That
allow-list is the kind of policy the built-in's `## Actions` placeholder asks
the repository owner to define.

## Look it up live

This file says what to reach for and what to be careful about. For the facts
themselves, ask the tool, and tell the user if it disagrees with this file:

- **Flags:** `bruin <command> --help`. The docs lag the CLI. For this skill,
  `bruin validate --help` and `bruin lineage --help`.
- **Docs:** the local Bruin MCP server, `bruin_get_doc_content('<path>')`, or
  `https://getbruin.com/docs/bruin/<path>.html` without it. For this skill:
  `commands/validate` for validation and its dry-run limits, `commands/lineage`
  for downstream references, `assets/materialization` for what each
  materialisation field changes, and `commands/cloud` for Cloud validation
  errors.
- **The user's environment:** Bruin Cloud MCP, or
  `bruin cloud ... --output json`.

## Access

Static local commands are allowed here because this skill edits repository
files: `bruin validate <path> --output json` and `bruin lineage <asset-file>
--output json --full`. Operational local runs are not. Use
`bruin cloud ... --output json`, or the Bruin Cloud MCP server when the host has
it, for Cloud context.

**Credentials.** Never ask for one in chat or pass one as a command argument.
For a source, the user runs `bruin connections add` with no flags (the
interactive prompt; its flag mode puts the secret on the command line) or
references `${VAR}` in `.bruin.yml`. For Cloud, `bruin cloud login` or an
exported `BRUIN_CLOUD_API_KEY`, never `--api-key`. `bruin auth status` shows
which is active without printing it.

## When to use

- A diagnosis recommends a repository change and a finding file records it.
  The diagnosis usually comes from a built-in skill such as
  `schema-drift-check`, `quality-check-investigate`, `duplicate-investigate` or
  `freshness-check`, with the finding file written by the orchestrating agent.
- A scheduled tick found an allow-listed task, such as a dependency patch bump.
- Someone explicitly asked for a routine maintenance PR.

Do not use for feature work, refactors, anything that changes pipeline
behaviour in a way a user would notice, or any change with no finding file
behind it. New behaviour needs a human-authored design.

## Inputs

| Input | Required | Example | Notes |
|---|---|---|---|
| `finding_file` | yes | `.context/drift-raw.orders-20260522.yml` | Must exist and parse. Written by the orchestrating agent when the diagnosis came from a built-in skill |
| `branch_name` | no | `self-healing/column-rename/orders-20260522` | Derived from the finding if absent. Must start with `self-healing/` |
| `draft` | no | `true` | Default `true`. Non-trivial changes land as drafts |

## Allowed change types

Only these are auto-allowed. Anything else is a human task.

| Change | Approval |
|---|---|
| `column-add`, a declared column that exists in source but not in the asset | auto |
| `column-rename`, across asset YAML and all downstream SQL | auto if 5 or fewer downstream references, otherwise approval |
| `column-remove`, a column no longer in source | approval if anything downstream references it |
| `type-widen`, for example `int` to `bigint` | auto |
| `type-narrow`, any narrowing | never auto, escalate |
| `check-threshold-adjust`, loosening a threshold on documented evidence | approval |
| `custom-check-create` or `custom-check-update` | approval |
| `asset-description-update`, documenting cadence, freshness or caveats | approval |
| `column-description-update` | auto if non-behavioural, approval if tied to a check or contract |
| `dedup-window-adjust` | approval |
| `dependency-bump`, patch version of an allow-listed dependency | auto |
| `dependency-bump-minor-or-major` | approval |
| `dead-code-removal`, an asset with no consumers and no successful run in 90 days | approval |

## Pre-flight checks

Before creating a branch:

1. The finding file exists, parses, and names a recognised action and
   recommendation.
2. The working tree is clean and sitting on the configured base branch.
3. No open PR already covers this finding. If one exists, comment on it rather
   than opening a second.
4. Recent PRs and commits touching the same assets have been reviewed, so this
   change does not duplicate, conflict with or mask a recent one.
5. The change type is on the allow-list. If not, abort with a structured
   escalation written back into the finding file.
6. Validation scope is decided. Asset-only validation is faster, but pipeline
   validation is required when dependency definitions, downstream SQL, pipeline
   defaults or shared config changed. For pipelines with variants, validate
   every affected variant or pass `--variant <variant>` explicitly.
7. Cloud validation errors have been checked, and any unrelated active errors
   are noted in the PR body.
8. The diff contains no credential-shaped strings. Any match aborts.
9. Any change to materialisation strategy, `primary_key`, `update_on_merge`,
   `merge_sql` or `incremental_key` has explicit human approval, because those
   change how Bruin writes data. `assets/materialization` says what each field
   does.

## PR construction

Branch: `self-healing/<change-type>/<short-slug>-<YYYYMMDD>`.
Title: `[self-healing] <change-type>: <one-line summary>`, 80 characters or
fewer. The commit message carries the triggering skill, the finding path, the
affected assets and the downstream impact count.

The PR body needs six sections: what the change does; why, quoting the evidence
from the finding; what triggered it, naming the skill, the finding path and the
detection time; scope, listing files, affected assets, downstream consumers
updated here, and downstream consumers deliberately not updated; verification;
and rollback.

Verification is a checklist, and every box is a claim you must be able to
support:

- `bruin validate <path> --output json` passed, with `--variant` where it
  applies. A `--fast` run skips query validation, so it is not a pass. Dry-run
  validation (automatic on BigQuery and Snowflake) can fail for a column the
  change adds before it exists in the destination, which is the normal state
  for `column-add` and `column-rename`. Record that as an expected false
  negative with the error quoted, not as a pass. Against an environment named
  `production`, validation stops for a confirmation prompt, and `--force`
  skips it; passing `--force` is production access, not a formality.
- Quality checks passed, but only if Cloud state confirms it or
  `bruin run --only checks <asset-file>` was actually run. Otherwise mark them
  not executed.
- Tested end to end in a development, shadow or sandbox environment, or
  explicitly marked `NOT TESTED END TO END, MUST BE TESTED BEFORE DEPLOYMENT`
  when no safe environment exists.

Never write "should fix" or "may resolve". State what the change does and what
evidence supported it. Anything beyond that is speculation dressed as a review
note.

## Guardrails

- **Allowed**: branch creation, edits scoped to the finding, `bruin validate`,
  Cloud validation-error inspection, commit, push, and `gh pr create --draft`.
- **Requires approval**: non-draft PRs, every change type marked approval
  above, force-pushing an existing PR, opening more than three PRs in one
  invocation, and any end-to-end test touching production.
- **Never**: merging, which is always a human action; pushing to the base
  branch; editing files outside the finding's declared scope; opening a PR with
  no finding file; claiming checks passed without evidence; claiming end-to-end
  coverage that does not exist; operational local runs.

If no safe non-production environment exists, say so in the PR body and in the
returned result rather than testing against production. Running an end-to-end
test against production needs a human to approve it first.

## Verification

A PR is open when the URL is returned, CI has started or is recorded as not
configured, the finding file has been updated with the PR URL, and the
end-to-end test status is recorded either way.

The PR is never "verified". Only humans verify. This skill's job ends when the
PR is waiting for review.

## Output

Return the PR URL, branch, finding path, change type, draft flag, files
changed, affected assets, downstream consumers not updated, CI status,
validation status, and end-to-end test status.

If the PR could not be opened, say which pre-flight check failed. "Tried and
failed" is a valid outcome. "Silently skipped" never is. Then call
[`pipeline-report`](../pipeline-report/SKILL.md).
