---
name: pipeline-report
description: Use when a self-healing pipeline run finishes, including a run where nothing was wrong, and a human needs one structured status, incident or digest message posted to the chat destination the user configured. Aggregates the findings other skills wrote. Sends outbound messages, so it asks before posting.
---

# Pipeline report

**Status:** experimental · **Risk:** approval-required

> **Upstream documentation wins.** Where this file disagrees with the
> [Bruin docs](https://getbruin.com/docs/bruin/overview.html) or `bruin --help`,
> upstream is right and this file is stale. Written against Bruin CLI
> `v0.11.765`, checked 2026-09-30.

Every run ends here. Whether the agent did something or decided to do nothing,
a human must be able to read one message and know what happened, what changed,
and what still needs attention.

## Look it up live

This file says what to reach for and what to be careful about. For the facts
themselves, ask the tool, and tell the user if it disagrees with this file:

- **Flags:** `bruin <command> --help`. The docs lag the CLI.
- **Docs:** the local Bruin MCP server, `bruin_get_doc_content('<path>')`, or
  `https://getbruin.com/docs/bruin/<path>.html` without it. For this skill:
  `cloud/notifications` for team notification rules,
  `cloud/legacy-notifications` for the `notifications:` block in pipeline files,
  and `commands/cloud` for `notification-rules` and run lookups.
- **The user's environment:** Bruin Cloud MCP, or
  `bruin cloud ... --output json`.

## Unverified

Two things this skill assumes and cannot check for you.

**You have some way to post a message.** This skill decides *what* to say and
*where* it should go. It does not ship a transport. If no chat integration is
available to you, write the report to `.context/` and tell the user where it is
rather than silently doing nothing.

**The `notification-rules list` response.** `commands/cloud` documents the rule
shape (`name`, `enabled`, `subscriptions`, `deliveries`), and the Cloud MCP
`notification-rule-schema` tool returned the same fields. `list` and `schema`
need a token with the `notification-rule:list` ability. What `list` returns
around each rule, such as IDs, was not checked against a live response. Run
`bruin cloud notification-rules schema` and `list` and read the actual shape
before relying on any field. If it differs, follow the tool and say so.

## Access and approval

Posting to chat is outside the Bruin CLI. It goes through whatever chat
integration the agent has, and it is an outbound action.

**Get approval before the first post of a session, and before any post at
`critical` severity.** Show the exact destination and the exact message body,
and wait. Do not post to a destination the user has not confirmed.

Use `bruin cloud ... --output json`, or the Bruin Cloud MCP server when the host
has it, when the report needs run IDs or asset names.

**Credentials.** Never ask for one in chat or pass one as a command argument.
For a source, the user runs `bruin connections add` with no flags (the
interactive prompt; its flag mode puts the secret on the command line) or
references `${VAR}` in `.bruin.yml`. For Cloud, `bruin cloud login` or an
exported `BRUIN_CLOUD_API_KEY`, never `--api-key`. `bruin auth status` shows
which is active without printing it.

## Never put these in a message

API tokens, connection values, `BRUIN_CLOUD_API_KEY`, any `api_token` field,
connection strings, credential file paths, raw command output that might carry
any of those, and row-level data samples. Redact before you compose, not after.
A message is not revocable once it is sent.

## When to use

- The end of any run, including runs where no action was taken.
- A specialist skill produced a finding that needs human attention.
- A scheduled digest is due.
- An explicit escalation from another skill.

Do not use for ordinary conversation, for posting raw query results with no
summary, or in place of a PR review comment.

## Inputs

| Input | Required | Example | Notes |
|---|---|---|---|
| `channel` | no | `<your-slack-channel-id>` | A channel ID the user configured. Never a guess |
| `severity` | yes | `info`, `warn`, `error`, `critical` | Drives format and mentions |
| `subject` | yes | `Schema drift: raw.orders` | One line, 80 characters or fewer |
| `source_files` | no | `[.context/drift-...yml]` | Finding files to summarise |
| `thread_ts` | no | `1700000000.000100` | Set when updating an existing thread |
| `mentions` | no | `[<oncall-handle>]` | Only on `error` and `critical` |

## Resolving the destination

Take the first that is available:

1. The destination supplied by the calling run or agent context.
2. Notification configuration that covers this pipeline. Team-level rules
   come from `bruin cloud notification-rules list --output json`; a rule
   covers this pipeline if its selector matches it or it has no selector, so
   read the selector rather than assuming. Older setups use a `notifications:` block in
   `pipeline.yml` or on assets (`cloud/legacy-notifications`). Channels named
   in either are configured, not inferred.
3. An explicit `channel` from the caller.
4. A channel ID the user has recorded in this project's own configuration.

If none of these yields a destination, **do not post.** Write the report to
`.context/`, say plainly that delivery was skipped because no destination was
configured, and return that as an escalation for whoever owns the
configuration. Never fall back to a channel name, a general alerts channel, or
anywhere you inferred rather than were told.

## Severity

| Severity | Mentions | Meaning |
|---|---|---|
| `info` | none | Routine. Did a thing, all fine |
| `warn` | none | Needs eyes within a day |
| `error` | on-call, only if context supplied a handle | Active impact, needs eyes within the hour |
| `critical` | on-call, only if context supplied a handle | Customer-visible or data integrity at risk. Approval required before posting |

Never silently upgrade or downgrade severity. The caller picks it.

## Message shape

```
:<severity-emoji>: *<subject>*
Pipeline: `<pipeline>` · Time: `<UTC timestamp>` · Run: `<handle>`

*What happened*
Two or three sentences, plain English, no jargon a new on-call would not know.

*What was done*  (omit if no action was taken)
- One bullet per concrete action, with PR URLs, run IDs and intervals.

*What needs attention*  (omit if empty)
- One bullet per item, each naming the person, team or skill to follow up.

*Evidence*
- Finding, diagnosis and run log links.

*Suggested follow-up*  (optional)
- One sentence. The next sensible action, not a menu of options.
```

Rules that decide whether the message is useful:

- Lead with the subject. No greeting.
- Never write "I noticed", "it appears" or "looks like". State what is true and
  state what is uncertain, each with its evidence.
- Quote numbers, not impressions. "Row count fell 47%, 4.2M to 2.2M", not "row
  count is way down".
- Link, do not paste. Long errors go in a thread reply.
- No emoji beyond the severity indicator.

For a scheduled digest, use a different shape: pipelines scanned, healthy and
with issues; what was resolved this window, one line each with a link; what is
still open, with owner; and recurring patterns, only where two or more similar
issues appeared. Digests are `info` or `warn` only. Anything critical was
already posted when it was detected.

## Method

Validate the inputs and abort with the reason if they do not hold. Resolve the
destination, and write a file-only report if there is none. Load and summarise
each source file. Build the body. Then check for a near-duplicate posted in the
last hour: if one exists, reply in its thread prefixed "Repeat detection"
rather than posting again. Post, then annotate every source finding file with
the resulting permalink so later skills can link back.

## Guardrails

- **Allowed**: composing the message, resolving the destination, reading
  finding files, writing the report record to `.context/`.
- **Requires approval**: the first post of a session, any `critical`, any post
  to a destination not previously confirmed by the user, and paging anyone.
- **Never**: posting to a destination that was inferred rather than configured;
  inventing a fallback channel; paging someone who is not on the current
  rotation; including secrets or row-level data; and suppressing a report
  because the previous one looked similar. Deduplicate by replying in thread.
  Never by dropping.

## Verification

The report is complete when the message returned a permalink, and every source
finding file carries that permalink. At `error` and above, an acknowledgement
is expected but not enforced by this skill. Humans own escalation from there.

## Output

Append one line per report to `.context/reports-<YYYY-MM-DD>.jsonl`, recording
the timestamp, destination, severity, subject, permalink and source files. That
record is how the agent answers "have we already told someone about this"
without scanning chat history each time.

This closes the chain that starts at
[`pipeline-triage`](../pipeline-triage/SKILL.md) and runs through
[`anomaly-investigate`](../anomaly-investigate/SKILL.md),
[`maintenance-pr`](../maintenance-pr/SKILL.md) and
[`pipeline-backfill`](../pipeline-backfill/SKILL.md).
