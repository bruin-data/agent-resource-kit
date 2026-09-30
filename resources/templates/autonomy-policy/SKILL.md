---
name: autonomy-policy
description: Use when deciding what an agent may do on its own in a repository, writing or reviewing an AGENTS.md autonomy section, setting up a self-healing or automated agent, or when a user asks how much freedom to give an agent over their systems.
---

# Autonomy policy

**Status:** experimental · **Risk:** read-only

> Your team's risk appetite wins over any
> default suggested here.

A template for the section of `AGENTS.md` that decides what an agent does on its
own. Fill it in with the user, paste it into their repository, and follow it.

Most projects never write this down, so the agent infers the boundary from tone,
which means it differs every session. Writing it once makes the boundary a
property of the repository rather than of the conversation.

## How to use it

Ask the user the four questions below, then write the filled-in template into
their `AGENTS.md`. Do not guess the answers. A policy the user did not choose is
worse than none, because it reads as though they did.

1. Which systems and environments are in scope, and which are explicitly out?
2. What may you do without asking?
3. What always needs a human first?
4. What must never happen, whatever the instruction?

If the user has no view yet, offer the defaults below as a starting point and say
they are deliberately conservative.

## The template

```markdown
## Agent autonomy policy

### Scope

- Systems: <the repos, pipelines, services in scope>
- Environments: <dev only, never production>
- Out of scope: <anything the agent must not touch, named>

### Do without asking

- Read: <files, logs, schemas, history>
- Query read-only, bounded: <which connections, what limits>
- Propose: a diff, a plan, a query, with reasoning shown
- Run validation that touches nothing

### Ask first

- Any write to <systems>
- Opening or merging a pull request
- Any outbound message: email, chat, webhook
- A run, rerun, or backfill
- Changing a schedule, schema, check threshold, or business definition
- A query materially more expensive than the last

### Never

- <destructive operations, named, with the consequence stated>
- Delete data, assets, connections or schedules
- Ask for or print a credential
- Change global agent, editor or MCP configuration

### Evidence every finding must carry

- What was inspected, with identifiers
- The command or query run, and against which environment
- What was expected against what was seen
- The action taken or proposed, and the result expected from it

### Stop and hand back when

- The evidence points two ways, or the cause is still a guess
- The root cause is a real business change rather than a defect
- A control this policy depends on is missing
- The fix would be larger than the problem reported

Who to ask: <team or person, and how to reach them>
```

## Getting the tiers right

**The `Never` bucket needs the consequence spelled out**, not just the command.
"Never `--full-refresh`" is forgettable. "Never `--full-refresh`: it discards the
daily snapshot history, which cannot be rebuilt" is not.

**`Ask first` is the bucket that decays.** Under time pressure people move things
into `Do without asking` and rarely move them back. Review it when the policy
has been in place a while, and treat a growing top bucket as a signal.

**Name the out-of-scope systems explicitly.** An agent reasoning about what is
"probably fine" is the failure this template exists to prevent. A list it can
check beats a judgement it has to make.

**Scope writes to a non-production environment.** This is the one line that turns
the policy from a request into a constraint, because it is enforced by the
credential rather than by the agent's cooperation.

## What a policy cannot do

An agent that ignores its instructions is not stopped by more instructions. This
template makes good behaviour the default and makes the boundary reviewable. It
is not a sandbox.

The controls that actually hold sit outside the agent: a read-only credential, a
separate development environment, the host's own permission prompts, and a human
reading the diff. Say so when a user asks whether the policy makes something
safe.
