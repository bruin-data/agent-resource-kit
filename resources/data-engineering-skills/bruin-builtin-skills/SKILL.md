---
name: bruin-builtin-skills
description: Use when a Bruin pipeline fails, data is stale, a quality check fires, duplicate rows or schema drift appear, or when building semantic models, and you need to know which maintained Bruin skill to install and reach for rather than improvising a diagnosis.
---

# Bruin's built-in skills

**Status:** experimental · **Risk:** read-only

> **Upstream documentation wins.** These skills ship with the Bruin CLI and are
> versioned with it, so the installed copy is always more current than this file.
> Run `bruin ai skills --help` and read the installed `SKILL.md` files. Written
> against Bruin CLI `v0.11.765`, checked 2026-09-30.

**Install Bruin's skills rather than writing your own diagnosis logic**, and
rather than copying them anywhere: they update with the CLI, and a copy goes
stale silently.

```bash
bruin ai skills all
```

## Look it up live

This file says what to reach for and what to be careful about. For the facts
themselves, ask the tool, and tell the user if it disagrees with this file:

- **Flags:** `bruin <command> --help`. The docs lag the CLI.
- **Docs:** the local Bruin MCP server, `bruin_get_doc_content('<path>')`, or
  `https://getbruin.com/docs/bruin/<path>.html` without it. For this skill:
  `commands/ai-skills` for which skills ship, where they install
  (`.agents/skills` or `.claude/skills`, depending on what the project already
  has), and how `AGENTS.md` is updated.
- **The user's environment:** Bruin Cloud MCP, or
  `bruin cloud ... --output json`.

The installed `SKILL.md` files are the source for what each skill does. Do not
hard-code the list of skills or their install path from memory or from this
file. Both change with the CLI.

## Which one to reach for

Read the `description:` line of each installed `SKILL.md` and pick by symptom.
Start at the symptom, not at the skill.

Never run `maintenance-action` before a diagnosis skill has established what is
wrong. That is how a confident fix gets applied to the wrong problem.

The starter troubleshooting skills each carry an `## Actions` section that is a
placeholder. Until the repository owner fills it in, the skill reports its
findings and stops. Read that section before expecting a skill to change
anything.

## Re-installing overwrites local edits

Re-running `bruin ai skills all`, or `bruin ai skills <name>`, rewrites each
selected skill directory whose files differ from the bundled copy. Anything you
wrote into it is removed, including a customised `## Actions` section. Before
re-running, copy local edits somewhere the installer does not touch, and re-apply
them after. `AGENTS.md` is different: Bruin replaces only its own marked section
there.

## What these do not cover

The built-in skills each handle one thing and return their result as text. They
write no file, and they do not decide which of them to run, gate a pull request,
bound a backfill, or tell anyone what happened. The orchestration skills in this
catalogue do that: `pipeline-triage`, `anomaly-investigate`, `maintenance-pr`,
`pipeline-backfill` and `pipeline-report`. See the
[folder index](../README.md) for which to use when.

## Before you install

A Bruin project must exist. If there is not one yet, start with the
`bruin-agent` skill: CLI install, project creation, template choice, and
connecting a source.

Bruin may offer to add placeholder Bruin Cloud and GitHub connections to
`.bruin.yml`. Skip that unless they are wanted.
