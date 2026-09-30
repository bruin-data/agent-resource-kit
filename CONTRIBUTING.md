# Contributing

What makes this catalogue worth reading is that someone has actually used every
resource in it. That is the bar. Most of what follows is mechanics for showing
it.

Resources you have used are welcome. So are bug reports, better wording, and "I
followed this skill and my agent did the wrong thing", which is often the most
useful issue we get.

## Before you build something

Open an issue first if it is substantial, so you do not duplicate something that
already exists upstream:

- **A Bruin data-source template** belongs in
  [bruin-data/bruin](https://github.com/bruin-data/bruin), where it is
  maintained alongside the CLI.
- **A Bruin data-engineering skill** may already exist. Run `bruin ai skills all`
  and check before writing one.

This repository says *which* tool to reach for and *what to be careful about*.
Where a file starts restating upstream documentation, that is a bug in the file.

## The shape of a resource

One folder, one `SKILL.md`, in the format agents already load:

```markdown
---
name: your-skill
description: Use when the user is doing X, asks about Y, or needs Z. Covers ...
---

# Your skill

**Status:** experimental · **Risk:** read-only

> **Upstream documentation wins.** Where this file disagrees with
> [the tool's docs](https://example.com) or its `--help` output, those are right
> and this file is stale. Written against <tool> `<version>`, checked <date>.

...
```

The rules the checker enforces:

- `name` matches the folder name, so a copied folder lands correctly.
- `description` starts with `Use when` and is 60 to 600 characters. It is a
  routing trigger, not a summary; nothing else belongs in frontmatter.
- A `**Status:** x · **Risk:** y` line, using the labels below.
- A resource file that drives a Bruin tool carries the upstream note, with the
  Bruin CLI version and date it was checked against. Any other upstream note
  carries a date. A file that drives no tool gets a one-line precedence note
  instead, saying what wins where it disagrees; the checker does not enforce
  that one.
- Every resource is listed in the root `README.md` index.
- Local links resolve, and no internal identifiers (Slack channel IDs, project
  ULIDs, service accounts) or forbidden files (`.bruin.yml`, `.env`) appear.

Push depth into sibling files referenced by relative path, so `SKILL.md` stays
short enough to load whole. The checker warns past 2,000 words.

## Choosing your labels

**Status.** Be conservative. Promoting later is easy.

| | Use when |
|---|---|
| `experimental` | It works for you. Start here. Most first contributions belong here. |
| `community` | You will maintain it and answer issues about it. |
| `stable` | Someone other than you has used it, and it records the upstream version it was checked against. |

**Risk.** The worst thing it can do when followed as written, not what you intend.

| | Use when |
|---|---|
| `read-only` | It reads, and produces local files. |
| `approval-required` | It can write, and every write is gated on explicit approval. |
| `write-capable` | It writes or sends without a built-in gate. Say so prominently. |

A risk level describes instructions, not a sandbox. See [`SECURITY.md`](SECURITY.md).

## What will get a pull request closed

1. **Credentials, anywhere.** No keys, no tokens, no `.bruin.yml`, no `.env`.
   Not expired ones, not in an example. Both the checker and gitleaks will catch
   most of this; do not rely on them.
2. **Real business data.** No customer records, no real revenue, no production
   output, no anonymised extract of a real dataset. Anonymisation fails more
   often than people expect, and this repository is public.
3. **Anything that asks a user to paste a credential into a conversation.** Use
   browser OAuth, an interactive local prompt, an environment variable
   reference, or a secret manager.
4. **Anything that modifies global agent, editor or MCP settings** without the
   user approving the exact change.
5. **Documented behaviour you did not observe.** Run the command, use what it
   printed. If you could not check something, say it is unverified rather than
   writing it as though you had.

## Writing a resource people keep

The difference between a resource someone uses twice and one they try once is
usually what it admits.

- **Say what the tool cannot do.** The analytics skills in `startup-data-kit`
  have a "what this cannot tell you" section, because the alternative is an
  agent producing a confident answer to a question the data cannot answer.
- **Say what the user has to decide.** `revenue-analytics` has ten decisions it
  cannot make for you, because MRR genuinely depends on them. A resource that
  picks silently teaches the user that a hard question is settled.
- **Name the traps specific to that data.** Generic advice gets skipped. "GA4
  thresholding means totals will not equal the sum of a breakdown" does not.
- **Write to the agent, imperatively.** Not prose about the tool.

## Say what you could not check

If a resource makes a claim you did not verify, give it an `## Unverified`
section saying which claim, why you could not check it, and what the reader
should run to confirm.

This is not a disclaimer. It is the difference between a reader who runs one
command to confirm a field name and a reader who finds out in production that it
changed. Resources here already use it for API shapes taken from documentation
rather than a live call, and for tools that need credentials the author did not
have.

A resource with nothing unverified does not need the section. A resource with
something unverified and no section is the problem this convention exists to
prevent.

## Before opening a pull request

```bash
./tests/check.py
```

No dependencies. It checks frontmatter, status labels, upstream notes and their
dates, index completeness, local links, and forbidden files.

Then say, in the pull request: what the resource does in one sentence, what you
ran to verify it, which status and risk you chose and why, and anything you
could not test. That last one is genuinely useful. "I could not test the Codex
path" gets a resource merged with an accurate description; silence gets it
merged with a wrong one.

## Review

Every contribution is reviewed for the same four things, in order:

1. **Safety.** Credentials, scopes, what needs approval, and whether the text
   tries to instruct an agent to do something the user did not ask for. This
   repository is read by agents, so instruction injection is reviewed for
   specifically.
2. **Honesty.** Does it do what it says, and does it say what it will not do.
3. **Shape.** Frontmatter, labels, upstream note, index entry, working links.
4. **Usefulness.** Would someone who did not write it get a good result.

Reviews are on the work. If something is not merged, the reason will be specific
enough to act on.

## Security problems

Do not open an issue. See [`SECURITY.md`](SECURITY.md).
