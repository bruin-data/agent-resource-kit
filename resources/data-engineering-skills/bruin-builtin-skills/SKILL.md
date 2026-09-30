---
name: bruin-builtin-skills
description: Use when a Bruin pipeline fails, data is stale, a quality check fires, duplicate rows or schema drift appear, or when building semantic models, and you need to know which maintained Bruin skill to install and reach for rather than improvising a diagnosis.
---

# Bruin's built-in skills

**Status:** experimental · **Risk:** read-only

> **Upstream documentation wins.** These skills ship with the Bruin CLI and are
> versioned with it, so the installed copy is always more current than this file.
> Run `bruin ai skills --help` and read the installed `SKILL.md` files. Written
> against Bruin CLI `v0.11.765`, checked 2026-09-29.

Bruin ships seven maintained skills. **Install them rather than writing your own
diagnosis logic**, and rather than copying them anywhere: they update with the
CLI, and a copy goes stale silently.

```bash
bruin ai skills all
```

Installs into `.agents/skills/` plus a repository-level `AGENTS.md`. Name one to
install just that: `bruin ai skills freshness-check`.

Re-running updates in place. If `AGENTS.md` already exists, Bruin replaces only
its own marked section, so anything you added around it survives.

## Which one to reach for

| Symptom | Skill |
|---|---|
| A pipeline, asset or command failed and the cause is unclear | `pipeline-diagnose` |
| Data is stale, or a scheduled run did not happen | `freshness-check` |
| A quality check failed or started warning unexpectedly | `quality-check-investigate` |
| Duplicate rows, unstable primary keys, repeated ingestion | `duplicate-investigate` |
| Source, destination or declared columns may have changed | `schema-drift-check` |
| A diagnosis is done and a controlled fix needs defining | `maintenance-action` |
| Building or querying semantic models, metrics, dimensions, joins | `bruin-semantic-layer` |

Start at the symptom, not at the skill. Running `maintenance-action` before a
diagnosis skill has established what is wrong is how a confident fix gets applied
to the wrong problem.

## What these do not cover

The built-in skills diagnose and fix one thing at a time. They do not orchestrate:
there is no router that decides which of them to run, no gate before opening a
pull request, no safety check before a backfill, and no reporting step.

The other skills in this folder fill exactly that gap. Use them together:

| Need | Skill |
|---|---|
| Something is broken, work out what and route it | `pipeline-triage` |
| A metric moved but nothing failed | `anomaly-investigate` |
| Turn a proposed fix into a reviewed pull request | `maintenance-pr` |
| Rerun a range safely after a fix | `pipeline-backfill` |
| Tell a human what happened | `pipeline-report` |

## Before you install

A Bruin project must exist. If there is not one yet, start with the
`bruin-agent` skill: CLI install, project creation, template choice, and
connecting a source.

Bruin may offer to add placeholder Bruin Cloud and GitHub connections to
`.bruin.yml`. Skip that unless they are wanted.

## Reference

- AI skills: https://getbruin.com/docs/bruin/commands/ai-skills.html
- Quality checks: https://getbruin.com/docs/bruin/quality/overview.html
- Semantic layer: https://getbruin.com/docs/bruin/core-concepts/semantic-layer.html
