# agent-resource-kit

**Open-source skills for AI agents.** Drop a folder into your project and your
agent knows how to do the thing.

Each resource is a `SKILL.md` in the format Claude Code, Cursor, Codex and
others already load automatically. Two kinds, mixed freely:

- **Pointers** to tools that already exist, so an agent reaches for the
  maintained thing instead of reinventing it.
- **Task skills** for judgement no tool encodes.

**[Join the Slack community](https://join.slack.com/t/bruindatacommunity/shared_invite/zt-3cymzktqu-bvFxPGyQHpvi~dok_W0L3w)**
to ask questions, work through a setup with someone, and share what you have
built with these. If a skill sent your agent somewhere unhelpful, that is worth
saying there as much as in an issue.

> **Example code, provided as-is.** This repository is not part of the Bruin
> platform, not a supported Bruin product, and not covered by any support
> agreement or SLA. It is documentation and sample scripts: it stores no customer
> data, holds no credentials, and has no access to any production system. Scripts
> run on your own machine, under your own credentials, configured by you. See
> [LICENSE](LICENSE) for the warranty disclaimer.

## Resources

**Setup**

| Resource | Status | Risk | Use it when |
|---|---|---|---|
| [`bruin-agent`](resources/bruin-agent/) | experimental | read-only | Installing the Bruin CLI, creating a project, choosing a template, connecting a source, registering the Bruin MCP server, installing Bruin's agent skills |

**[`startup-data-kit`](resources/startup-data-kit/)**: an agent works with you
to set up and customise a Bruin template for your startup, then answers
questions from it. One domain per folder:

| Resource | Status | Risk | Use it when |
|---|---|---|---|
| [`revenue-analytics`](resources/startup-data-kit/revenue-analytics/) | experimental | approval-required | MRR, churn, expansion, failed payments, cash collection. Stripe, Chargebee, Paddle |
| [`marketing-analytics`](resources/startup-data-kit/marketing-analytics/) | experimental | approval-required | CAC, ROAS, attribution, campaigns, CRM pipeline. Google Ads, Meta, HubSpot, Klaviyo |
| [`product-analytics`](resources/startup-data-kit/product-analytics/) | experimental | approval-required | Activation, feature adoption, retention, usage-based churn signals. PostHog, Mixpanel, Amplitude |
| [`web-analytics`](resources/startup-data-kit/web-analytics/) | experimental | approval-required | Traffic, landing pages, channels, funnel drop-off. GA4, Search Console |
| [`ai-search-visibility`](resources/startup-data-kit/ai-search-visibility/) | experimental | approval-required | SEO, GEO and AEO. Search Console, AI crawler traffic, whether assistants mention you |

**[`data-engineering-skills`](resources/data-engineering-skills/)**: keeping
pipelines healthy. Install Bruin's seven maintained skills, then add the
orchestration layer they do not ship:

| Resource | Status | Risk | Use it when |
|---|---|---|---|
| [`bruin-builtin-skills`](resources/data-engineering-skills/bruin-builtin-skills/) | experimental | read-only | Working out which maintained Bruin skill to install and reach for |
| [`pipeline-triage`](resources/data-engineering-skills/pipeline-triage/) | experimental | read-only | Something broke and you need to work out what, and route it |
| [`anomaly-investigate`](resources/data-engineering-skills/anomaly-investigate/) | experimental | read-only | A metric moved but nothing failed |
| [`maintenance-pr`](resources/data-engineering-skills/maintenance-pr/) | experimental | approval-required | Turning a proposed fix into a reviewed pull request |
| [`pipeline-backfill`](resources/data-engineering-skills/pipeline-backfill/) | experimental | approval-required | Rerunning a date range safely after a fix |
| [`pipeline-report`](resources/data-engineering-skills/pipeline-report/) | experimental | approval-required | Telling a human what happened |

**[`coding-agent-workflows`](resources/coding-agent-workflows/)**: repeatable
work on a codebase.

| Resource | Status | Risk | Use it when |
|---|---|---|---|
| [`generate-changelog`](resources/coding-agent-workflows/generate-changelog/) | experimental | read-only | You need customer-facing release notes from git history |
| [`record-terminal-demo`](resources/coding-agent-workflows/record-terminal-demo/) | experimental | approval-required | You need a terminal demo of a CLI recorded with VHS, rendered and visually checked |

**[`tools`](resources/tools/)**: sample scripts an agent can shell out to. These
ship code you run yourself, with your own credentials.

| Resource | Status | Risk | Use it when |
|---|---|---|---|
| [`attio-cli`](resources/tools/attio-cli/) | experimental | approval-required | Reading or updating records, lists and attributes in an Attio CRM |
| [`blog-image-generator`](resources/tools/blog-image-generator/) | experimental | approval-required | Finding a licence-friendly Unsplash photo and turning it into a cropped, treated cover image |
| [`linkedin-enrichment`](resources/tools/linkedin-enrichment/) | experimental | approval-required | Pulling public LinkedIn company, person, post or job data through paid Apify actors |

Everything is `experimental` today: the commands in `bruin-agent` were verified
against a live Bruin CLI, and the connector and template lists came from Bruin's
own tooling, but nobody other than the author has used any of these end to end.
A resource becomes `stable` when someone else has.

**Risk** is the worst a resource can do when followed as written. `read-only`
reads and produces local files. `approval-required` can write, run or send
something, and every such action is gated on your explicit approval. [`SECURITY.md`](SECURITY.md) explains what the labels do
and do not guarantee.

## Use it

**Copy the folder.** Your agent picks it up with no further setup.

```bash
git clone https://github.com/bruin-data/agent-resource-kit
cp -R agent-resource-kit/resources/bruin-agent ~/my-project/.claude/skills/
cp -R agent-resource-kit/resources/startup-data-kit/revenue-analytics ~/my-project/.claude/skills/
```

`.claude/skills/` for Claude Code, `.agents/skills/` for several others.
Bruin's own `bruin ai skills` uses whichever of the two the project already has,
and links both if both exist
([`commands/ai-skills`](https://getbruin.com/docs/bruin/commands/ai-skills.html)).
Skills are independent; take only what you need.

**Or hand your agent the link.**

```text
Read https://github.com/bruin-data/agent-resource-kit and use whatever fits:
I need to work out why our MRR stopped growing last quarter.
```

It reads the index, then the one skill it needs.

## Upstream documentation is the source of truth

Every file here is a snapshot of how something worked the day it was written.
Where a resource disagrees with the tool's own documentation or its `--help`
output, **upstream is right and the file here is stale.** Each resource says
which version and date it was written against, and instructs the agent to check
upstream and tell you when it finds a difference.

These resources exist to say which tool to reach for and what to be careful
about. They are not a second copy of anyone's manual.

## What these are written to prevent

The failure mode with agents and business data is not an error message. It is a
confident, well formatted, wrong number that someone forwards to an investor.

So each skill covers the definitions that change the answer, the traps specific
to that data, what the source genuinely cannot tell you, and what needs a
human's approval. They point at maintained tools rather than reimplementing
them, and link to upstream documentation rather than restating it so it cannot
go stale.

## Credentials

**Nothing here will ask you to paste a credential into a chat**, and every skill
tells the agent not to.

A key sent in conversation sits in the transcript, likely in provider logs, and
in the agent's context for the rest of the session where it can resurface in a
summary or a generated file. You cannot revoke it from a transcript, only from
the provider. A key passed as a command flag is in your shell history and the
process list.

Use browser OAuth, an interactive local prompt such as `bruin connections add`,
an environment variable reference, or your secret manager. Ask for read-only
scopes. A scoped credential is the control that actually holds; instructions in
a file are not a sandbox.

This repository contains no credentials and no real business data.

## Contributing

Resources you have actually used are welcome. [`CONTRIBUTING.md`](CONTRIBUTING.md)
has the shape, the labels, and what gets rejected.

```bash
./tests/check.py
```

No dependencies. It checks frontmatter, status labels, upstream notes and their
dates, index completeness, local links, and files that must never be committed.
CI runs it on every change, scans for credentials with gitleaks, and checks
external links weekly so a dead upstream link surfaces on its own.

## Licence

MIT. See [LICENSE](LICENSE).
