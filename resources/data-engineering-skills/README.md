# Data engineering skills

Keeping pipelines healthy: diagnosing failures, investigating anomalies, and
recovering safely.

> **Upstream documentation wins.** Where a skill disagrees with the
> [Bruin docs](https://getbruin.com/docs/bruin/overview.html) or `bruin --help`,
> upstream is right and the file here is stale. Checked 2026-09-29.

## Start by installing Bruin's own skills

Bruin ships seven maintained diagnosis skills with the CLI. Install them; do not
copy them anywhere:

```bash
bruin ai skills all
```

[`bruin-builtin-skills`](bruin-builtin-skills/) is the pointer: what each one
covers, and which symptom sends you to which.

## Then add the orchestration layer

The built-in skills each diagnose one thing. They do not decide which to run,
gate a pull request, bound a backfill, or tell anyone what happened. These five
do, and that is the only reason they exist here:

| Resource | Risk | Use it when |
|---|---|---|
| [`pipeline-triage`](pipeline-triage/) | read-only | Something is broken and you need to work out what, and route it |
| [`anomaly-investigate`](anomaly-investigate/) | read-only | A metric moved but nothing failed and no check fired |
| [`maintenance-pr`](maintenance-pr/) | approval-required | A prior skill proposed a fix and it needs to become a reviewed pull request |
| [`pipeline-backfill`](pipeline-backfill/) | approval-required | A fix has merged and a date range needs rerunning safely |
| [`pipeline-report`](pipeline-report/) | approval-required | A human needs to know what happened |

The chain:

```text
triage -> diagnose (built-in) -> investigate (built-in) -> maintenance-pr
       -> backfill -> report
```

Start at `pipeline-triage` when an alert fires or someone asks what is broken.
Start at `anomaly-investigate` when the pipeline is green and the number is not.

## The `.context/` handoff is a convention, not a feature

These skills pass findings to each other by writing a YAML file into `.context/`
and returning its path. Nothing enforces that. No tool creates the directory, no
schema validates the file, and nothing stops a skill inventing a shape the next
one cannot read.

It works because each skill states what it writes and what it expects to read.
If you change one, read the others. If a file is missing or will not parse,
**stop and say so** rather than proceeding on a guess: a maintenance PR built on
a finding that did not load is worse than no PR.

Add `.context/` to your `.gitignore`. These files are working notes about your
systems, not artefacts to commit.

## Why three of these need approval

`maintenance-pr` opens pull requests, `pipeline-backfill` replaces data, and
`pipeline-report` sends outbound messages. Each is gated on explicit approval and
says so in its own file. A risk level describes what a resource instructs, not a
sandbox; see [`../../SECURITY.md`](../../SECURITY.md).
