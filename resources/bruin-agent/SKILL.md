---
name: bruin-agent
description: Use when setting up Bruin for the first time, installing the Bruin CLI, creating a Bruin project, choosing a Bruin template, connecting a data source, registering the Bruin MCP server in Claude Code, Cursor, Codex or VS Code, or installing Bruin agent skills. Start here before any Bruin data work.
---

# Bruin agent setup

**Status:** experimental · **Risk:** read-only

> **Upstream documentation wins.** Where this file disagrees with the [Bruin
> docs](https://getbruin.com/docs/bruin/overview.html) or with `bruin <command>
> --help`, upstream is right and this file is stale. Written against Bruin CLI
> `v0.11.765`, checked 2026-09-30. Verify any template name, flag or connector
> before relying on it, and tell the user when you found a difference.

Get Bruin installed, a project created, a source connected, and the agent wired
up. Every other Bruin resource in this repository assumes this is done. Use
maintained Bruin templates and skills rather than writing ingestion or agent
instructions from scratch.

## Look it up live

This file says what to reach for and what to be careful about. For the facts
themselves, ask the tool, and tell the user if it disagrees with this file:

- **Flags:** `bruin <command> --help`. The docs lag the CLI.
- **Docs:** the local Bruin MCP server, `bruin_get_doc_content('<path>')`, or
  `https://getbruin.com/docs/bruin/<path>.html` without it. For this skill:
  `getting-started/introduction/installation` for installing, `commands/init`
  for project layout and `--merge`, `commands/connections` and
  `secrets/overview` for credentials, `commands/environments`,
  `commands/ai-skills`, `getting-started/bruin-mcp` and `cloud/mcp-setup` for
  MCP, `commands/query` and `core-concepts/semantic-layer`.
- **The user's environment:** Bruin Cloud MCP, or
  `bruin cloud ... --output json`.

For the command surface, start from `bruin --help` or `commands/overview`.
`docs`, `render-ddl`, `mcp` and `auth` have no docs page, so use `--help`.
Sources, templates, and what to do when neither fits:
[connectors.md](connectors.md).

## 1. Install the CLI

```bash
curl -LsSf https://getbruin.com/install/cli | sh
bruin version     # check
bruin upgrade     # update in place
```

For Windows, permission errors or an older install, read
`getting-started/introduction/installation` rather than guessing.

## 2. Create a project

```bash
mkdir ~/their-project && cd ~/their-project && git init
bruin init <template>
```

Run `git init` first so the project stays in the current folder. Without a
repository, `bruin init` creates a `bruin/` wrapper folder and runs `git init`
inside that. Either way the pipeline lands in a subfolder with `.bruin.yml` at
the repository root, and later commands take that pipeline folder as their path.

Never scaffold inside a clone of a public catalogue, and never inside another
Bruin project: a `.bruin.yml` higher up the tree gets picked up.

### Choose the destination before the source

The source is usually obvious. The destination decides whether a maintained
template exists at all.

| They already have | Do this |
|---|---|
| BigQuery, Snowflake, ClickHouse, Databricks, Postgres, Redshift, Athena | Model there. Keep the boundary they already run. |
| No warehouse, and a local template exists for the source | Use it. |
| No warehouse, no local template for the source | Do not improvise a local path. Say so and offer a small managed warehouse, or a different starting source. |

**There is no DuckDB template for Stripe.** The maintained Stripe paths are
`stripe-bigquery` and `stripe-databricks`. If someone wants Stripe locally, that
is a project, not a flag. Tell them.

### Pick a template, then read its README

Get the names from `bruin init --help`; [connectors.md](connectors.md) says how
to choose. Before the first run, read the template's README (the `README.md`
that `bruin init` writes into the pipeline folder, or
`getting-started/templates-docs/<name>-README`). It names the connections the
template needs and any first-load steps.

To add a second template, pass the existing pipeline folder:
`bruin init <template> <pipeline-folder> --merge`. It refuses if any template
file already exists there, and it leaves `pipeline.yml` alone, so keys the
template relies on may need copying across (`commands/init`). It does not
reconcile the two models. Joining one source to another depends on a stable
shared identifier existing; if it does not, say the join is the work rather
than a detail of it.

## 3. Connect the source

**Credentials.** Never ask for one in chat or pass one as a command argument.
For a source, the user runs `bruin connections add` with no flags (the
interactive prompt; its flag mode puts the secret on the command line) or
references `${VAR}` in `.bruin.yml`. For Cloud, `bruin cloud login` or an
exported `BRUIN_CLOUD_API_KEY`, never `--api-key`. `bruin auth status` shows
which is active without printing it.

This is deliberately stricter than Bruin's docs, whose examples pass
`--credentials` on the command line. A key sent in chat stays in the transcript,
provider logs and your context, and only the provider can revoke it. A key
passed as a flag is in shell history and the process list.

Your job is everything around it: write config with a `${VAR}` reference
(syntax in `secrets/bruinyml`), give the exact command, then run
`bruin connections test <name>` and report the result. For shared or deployed
setups, `secrets/overview` lists the supported secret backends. `.bruin.yml` is
gitignored by Bruin. Keep it that way.

Ask for the smallest scope that works. For Stripe that is a **restricted** key
with read access to the specific resources needed, never a live secret key. A
read-only credential makes read-only structural rather than a promise about your
behaviour.

## 4. Bound the first run, then run it

```bash
bruin validate <pipeline-folder>
bruin environments list
bruin run --environment <env> --start-date <from> --end-date <to> <pipeline-folder>
```

**Pick the environment.** Most templates create only `default`. For a separate
dev environment, propose `bruin environments create` or `clone`
(`commands/environments`) and let the user approve it. A clone copies every
connection from its source, so without a schema prefix or other credentials it
writes to the same place. Say which environment you used, every time.

**Pick the window.** Local `bruin run` takes it from `--start-date` and
`--end-date`, which default to yesterday. It does not read `start_date` in
`pipeline.yml`, which anchors Bruin Cloud schedules and catchup
(`pipelines/definition`). An asset-level `start_date` only affects ingestr
assets on `--full-refresh` (`assets/definition-schema`). Choose the range
deliberately and state the expected scan; twelve to eighteen months suits most
reviews.

**Follow the template's first-load steps.** `stripe-bigquery`, for example,
wants its first load run with `--full-refresh` so its snapshot tables exist, and
warns that repeating it later discards the accumulated history. `--full-refresh`
still needs the user's explicit go-ahead with that consequence named.

Then check it loaded the right data. A pipeline that ran successfully and a
pipeline that loaded the right data are different claims. Compare row counts and
the maximum date against the source's own dashboard.

## 5. Install the Bruin agent skills

```bash
bruin ai skills all
```

`commands/ai-skills` says where they land (`.agents/skills`, `.claude/skills`,
or both linked, depending on which folders exist) and what each covers. For the
live list without installing anything, run `bruin ai skills` with no argument in
a non-interactive shell: it prints the names and writes nothing. Name one to
install just that. Install `bruin-semantic-layer` before creating or editing
semantic models.

Re-running updates in place. If `AGENTS.md` exists, Bruin replaces only its own
marked section, so anything around it survives. Put business-specific guidance
outside that section. Skip the placeholder Bruin Cloud and GitHub connections
Bruin may offer unless they are wanted.

## 6. Register the MCP servers, optionally

Everything here works without them.

- **Local, `bruin mcp`:** Bruin's docs, nothing else. Three tools list and read
  doc pages; it runs no commands, reads no project, and works outside one.
  `getting-started/bruin-mcp` claims more and says a project is needed; tell the
  user if they rely on that. Show them the snippet for their host from that page.
- **Bruin Cloud MCP:** the user's pipelines, runs and connections. Setup in
  `cloud/mcp-setup`, tokens in `cloud/api-tokens`. With shell access,
  `bruin cloud` (`commands/cloud`) covers the same ground without MCP.

The Cloud page's Claude Code command puts a bearer token in a command argument,
and its Cursor and Codex snippets paste it into a config file. Both break the
credentials rule. Prefer the OAuth connector it describes for Claude Desktop and
Web, or a host setting that reads the header from an environment variable. Never
type the token for them.

**Do not edit agent, editor or MCP config without the user approving the exact
change.** `claude mcp add` defaults to `--scope local`; `--scope user` affects
every project and `--scope project` writes a `.mcp.json` into the repository.
The VS Code and Codex files in the Bruin docs are user-level; Cursor's can be
either. Show the snippet, say which file changes and what it affects, let them
apply it.

A local MCP server runs with your privileges: the filesystem, environment
variables, the network, and every credential you can see. Being local is not a
security property. Say so if asked.

## Working habits

**Validate, render, then run.** `bruin validate` catches structural problems
without touching data. `bruin render <asset>` shows the SQL that will execute,
templating resolved. Both are free.

**Query narrow first.** Only the columns needed, a bounded date range, a limit.
Run `bruin query --dry-run` before anything that might scan a lot, and always
pass `--description` saying why. Both flags are in `bruin query --help`, not in
`commands/query`. Semantic queries need `--semantic-model` with `--asset` or
`--pipeline`.

**Make assumptions fail loudly.** Quality checks run after each asset and block
downstream assets unless marked `blocking: false` (`quality/overview`). A check
is how a modelling assumption fails loudly instead of silently.

**Never print a credential.** `bruin connections list` shows names and which
fields are filled, not values. Keep your own output the same, including errors
and summaries.

**Stop and ask** before `--full-refresh`, a backfill, anything against
production, creating or changing an environment, any write to a source system,
any outbound message, and any new network destination.

## Symptoms

| Symptom | Cause |
|---|---|
| `no git repository found` | Not in a git repo. `git init`. |
| `no pipeline file found in '.'` | `run` needs the pipeline folder or an asset path, not the project root. |
| `environment 'dev' not found` | Most templates create only `default`. `bruin environments list`. |
| `destination connection '...' not found` | A `.bruin.yml` higher up the tree was picked up. Do not nest projects; `--config-file` forces one. |
| `Could not set lock on file ... .db` | Parallel assets on one DuckDB file. `--workers 1`. |
| `skill name is required in non-interactive mode` | The error lists the names. Pass one or `all`. |
| MCP tools missing after setup | The host needs a restart or reload. |
| First run loaded one day, or far too much | No date flags, or the wrong ones. Pass `--start-date` and `--end-date`. |

## Unverified

- **What `--scope local` means in Claude Code.** `claude mcp add --help` gives
  the scope names and the default, not their meaning. Run `claude mcp list`
  after adding and read the Claude Code MCP docs to confirm.
- **Reading the Cloud MCP header from an environment variable.** Not tested for
  any host. Check the host's MCP documentation before proposing it.
- **The DuckDB lock row.** Carried over, not reproduced: `duckdb-example` and
  `duckdb-lineage` ran with default workers on `v0.11.765`. If a DuckDB run
  fails with a lock error, retry with `--workers 1`.
