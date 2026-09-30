---
name: bruin-agent
description: Use when setting up Bruin for the first time, installing the Bruin CLI, creating a Bruin project, choosing a Bruin template, connecting a data source, registering the Bruin MCP server in Claude Code, Cursor, Codex or VS Code, or installing Bruin agent skills. Start here before any Bruin data work.
---

# Bruin agent setup

**Status:** experimental · **Risk:** read-only

> **Upstream documentation wins.** Where this file disagrees with the [Bruin
> docs](https://getbruin.com/docs/bruin/overview.html) or with `bruin <command>
> --help`, upstream is right and this file is stale. Written against Bruin CLI
> `v0.11.765`, checked 2026-09-29. Verify any template name, flag or connector
> before relying on it, and tell the user when you found a difference.

Get Bruin installed, a project created, a source connected, and the agent wired
up. Every other Bruin resource in this repository assumes this is done.

Use maintained Bruin templates and skills rather than writing ingestion or agent
instructions from scratch. Bruin ships tested templates with raw, staging and
reporting layers, column documentation and quality checks.

## 1. Install the CLI

```bash
curl -LsSf https://getbruin.com/install/cli | sh
```

Works on macOS, Linux, and Windows via Git Bash or WSL. Use `sudo sh` if it
reports a permission error. Homebrew is deprecated; uninstall any Homebrew copy
first.

```bash
bruin version     # check
bruin upgrade     # update in place
```

## 2. Create a project

```bash
mkdir ~/their-project && cd ~/their-project && git init
bruin init <template>
```

`git init` is required, not optional. Bruin locates a project by walking up to
the enclosing git repository. Never scaffold inside a clone of a public
catalogue, and never inside another Bruin project.

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

### Get the live template list

```bash
bruin init --help
```

Read the actual output. The catalogue changes and a list in a file goes stale.
See [connectors.md](connectors.md) for which sources exist and which templates
cover them.

To add a second template to an existing project:

```bash
bruin init --merge <template>
```

Merge adds assets, macros and config without overwriting. It does not reconcile
the two models. Joining one source to another depends on a stable shared
identifier existing; if it does not, say the join is the work rather than a
detail of it.

## 3. Connect the source

```bash
bruin connections add
```

**Never ask for a credential in conversation**, and never put one in a command
argument. A key sent in chat sits in the transcript, likely in provider logs,
and in your context for the rest of the session where it can resurface in a
summary or a generated file. It cannot be revoked from a transcript, only from
the provider. A key passed as a flag is in shell history and the process list.

Your job is everything around it: write config with a `${VAR}` reference, give
the exact command, then test the connection.

Ask for the smallest scope that works. For Stripe that is a **restricted** key
with read access to the specific resources needed, never a live secret key. A
read-only credential makes read-only structural rather than a promise about your
behaviour.

For deployed or shared setups use an environment variable reference or a
supported secret backend: Vault, Doppler, AWS Secrets Manager, Azure Key Vault.

`.bruin.yml` is gitignored by Bruin. Keep it that way.

## 4. Bound the first run, then run it

Set `start_date` in `pipeline.yml` **before** the first run, not after. An
unbounded first load is where warehouse bills surprise people. Twelve to
eighteen months suits most reviews.

```bash
bruin validate .
bruin run --environment dev .
```

Run in `dev` unless production was asked for by name, and say which environment
you used. Add `--workers 1` for DuckDB destinations, which take an exclusive
file lock.

Then check it loaded the right data. A pipeline that ran successfully and a
pipeline that loaded the right data are different claims. Compare row counts and
the maximum date against the source's own dashboard.

## 5. Install the Bruin agent skills

```bash
bruin ai skills all
```

Installs into `.agents/skills/` plus a repository-level `AGENTS.md`:

| Skill | Covers |
|---|---|
| `AGENTS.md` | Navigating pipelines and assets, environments and secrets, querying, creating and updating SQL assets, reporting |
| `bruin-semantic-layer` | Semantic models, metrics, dimensions, segments, joins |
| `pipeline-diagnose` | Failed runs |
| `schema-drift-check` | Source schema changes |
| `duplicate-investigate` | Duplicate rows |
| `freshness-check` | Stale data |
| `quality-check-investigate` | Failing quality checks |
| `maintenance-action` | Routine maintenance |

Name one to install just that: `bruin ai skills freshness-check`.

Re-running updates in place. If `AGENTS.md` exists, Bruin replaces only its own
marked section, so anything added around it survives. Append business-specific
guidance below that section rather than editing inside it.

Bruin may offer to add placeholder Bruin Cloud and GitHub connections. Skip
those unless they are wanted.

## 6. Register the MCP server, optionally

Lets you call the Bruin CLI directly instead of composing shell commands. It is
**optional**; everything works without it. A project must exist first.

| Host | Setup |
|---|---|
| **Claude Code** | `claude mcp add bruin -- bruin mcp` (project-scoped) |
| **Cursor** | Settings, MCP & Integrations, Add Custom MCP |
| **VS Code** | Command Palette, "Add MCP", Command (stdio), enter `bruin mcp` |
| **Codex CLI** | Edit `~/.codex/config.toml` |

Cursor:

```json
{ "mcpServers": { "bruin": { "command": "bruin", "args": ["mcp"] } } }
```

VS Code, in `mcp.json` (`~/.vscode/mcp.json` on macOS, `%APPDATA%\Code\mcp.json`
on Windows, `~/.config/Code/mcp.json` on Linux):

```json
{ "servers": { "bruin": { "type": "stdio", "command": "bruin", "args": ["mcp"] } }, "inputs": [] }
```

Codex CLI, in `~/.codex/config.toml`:

```toml
[mcp_servers.bruin]
command = "bruin"
args = ["mcp"]
```

All hosts need a restart or reload. On Windows use the full executable path, for
example `C:\Users\Name\.bruin\bin\bruin.exe`.

**Do not edit a global agent, editor or MCP config without the user approving
the exact change.** Claude Code's registration is project-scoped; Cursor, VS
Code and Codex are not, so a change there affects every project on the machine.
Show the snippet, say what it affects, let them apply it.

A local MCP server runs with your privileges. It reaches the filesystem,
environment variables, the network, and every credential you can see. Being
local is not a security property, and it is worth saying so if asked.

## Reference

Command surface and what to reach for when: [cli-reference.md](cli-reference.md).
Source and template catalogue: [connectors.md](connectors.md).

| Symptom | Cause |
|---|---|
| `no git repository found` | Not in a git repo. `git init`. |
| `destination connection '...' not found` | A `.bruin.yml` higher up the tree was picked up. Do not nest projects; `--config-file` forces one. |
| `Could not set lock on file ... .db` | Parallel assets on one DuckDB file. `--workers 1`. |
| `bruin ai skills` asks for a name | Non-interactive shell. Pass `all` or a skill name. |
| MCP tools missing after setup | The host needs a restart. |
| First run slow or expensive | No `start_date`. Set it and start over. |

- Installation: https://getbruin.com/docs/bruin/getting-started/introduction/installation.html
- Templates: https://getbruin.com/docs/bruin/getting-started/templates.html
- `bruin init`: https://getbruin.com/docs/bruin/commands/init.html
- Credentials: https://getbruin.com/docs/bruin/getting-started/credentials.html
- AI skills: https://getbruin.com/docs/bruin/commands/ai-skills.html
- Bruin MCP: https://getbruin.com/docs/bruin/getting-started/bruin-mcp.html
