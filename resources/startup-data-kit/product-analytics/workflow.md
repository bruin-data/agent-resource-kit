# Setting up a template with the user

> **Upstream documentation wins.** Where this file disagrees with the [Bruin
> docs](https://getbruin.com/docs/bruin/overview.html) or `bruin <command>
> --help`, upstream is right and this file is stale. Written against Bruin CLI
> `v0.11.766`, checked 2026-10-01.

Identical in every startup-data-kit skill. Work in order.

## Working with the user

- **Check before acting;** say what you found. Never redo working steps.
- **Ask before every write** (install, init, config, model, run); show the diff, wait for a yes.
- **Ask a few questions at a time,** each with its default and the term in plain words.
- **Do not guess.** If the user does not know, record the default as unconfirmed.
- **When only the user can do a step,** give exact steps and wait.
- **Record answers in `decisions.md` beside `pipeline.yml`:** choice, pick, confirmed or default, date.

## Look it up live

- Commands and flags: `bruin <command> --help`.
- Docs: Bruin MCP `bruin_get_doc_content` for `getting-started/templates-docs/<name>-README`, `ingestion/<source>`, `platforms/<warehouse>`; or `https://getbruin.com/docs/bruin/<path>.html`.
- The user's pipelines, runs and connections: Bruin Cloud MCP (`cloud/mcp-setup`), if they run Bruin Cloud.

## 1. Bruin is installed

`bruin version`. If `Latest` is newer than `Current`, offer `bruin upgrade`. If missing, ask, then `curl -LsSf https://getbruin.com/install/cli | sh`; on Windows or failure, read `getting-started/introduction/installation`.

## 2. The Bruin MCP server is connected

If you lack the `bruin_get_doc_content` tool, read `getting-started/bruin-mcp`.

- If you can edit the host's MCP config, show the exact command (Claude Code: `claude mcp add bruin -- bruin mcp`) and its project or global scope; run it only after approval.
- Otherwise give the user the snippet; the host usually needs a restart.

## 3. You are inside the user's own git repository

`git rev-parse --show-toplevel`.

- **Not a repository:** ask which folder, then `git init`; otherwise `bruin init` creates a `bruin/` wrapper with its own git.
- **A repository:** confirm it is the user's, not a public catalogue or another Bruin project (a parent `.bruin.yml` gets picked up).
- **Bruin project exists:** ask whether to add (`--merge`; read `commands/init`) or start fresh.

## 4. Confirm the warehouse

Ask where the data lands; do not pick. It decides which templates exist.

- **None yet:** list destinations this domain's templates support (`bruin init --help`) and their setup cost; some run on local DuckDB.
- **No template supports it:** say so; offer the closest template elsewhere, or ingestion alone. Never improvise one.

## 5. Choose the template

1. `bruin init --help` for current names; keep those matching source and warehouse.
2. Read each candidate's README; if none, say so and read the scaffolded `README.md`.
3. Tell the user what each builds, needs and omits. Let them choose.
4. After a yes, `bruin init <template>`. If it opens an interactive wizard, give the user the command.
5. Read the scaffolded files, run `bruin validate <pipeline-folder>`, and tell the user anywhere they disagree with the README or fail.

If nothing fits, say so; agree before building modelling yourself. If no pipeline is needed, say so.

## 6. Credentials into `.bruin.yml`

The README and assets name the connections. A sample's inline key is a shape, not a value.

**Never ask for a credential in chat or pass one as a command argument.** If the user pastes one, tell them to rotate it.

1. Read `ingestion/<source>` or `platforms/<warehouse>` for the fields.
2. Walk the user to the narrowest credential: read-only or restricted, never admin when narrower exists.
3. The user sets an env var (gitignored `.env` or secret manager); you write `${VAR_NAME}` (`secrets/bruinyml`). Or the user runs `bruin connections add` with no flags.
4. `bruin connections test --name <connection>`. Report the result, never the value.

`git check-ignore .bruin.yml`; if not ignored, stop and fix first. Bruin Cloud: `bruin cloud login` or exported `BRUIN_CLOUD_API_KEY`, never `--api-key`.

## 7. Work out what to ask

> **The questions come from the template, not from a list.** Templates change:
> variables are added, defaults move, reports appear and disappear. Do not work
> from a remembered or hard-coded set of questions, including any in these
> files. Read the template as it is today, list every choice it makes on the
> user's behalf, and decide which ones this user needs to confirm.

- Read the README, `pipeline.yml` variables, asset filters, checks, and report metric definitions.
- Drop choices that do not apply; `SKILL.md` is a lens, not a script.
- Add what the template cannot infer (test accounts, history needed); lead with what moves headline numbers.

## 8. Customise

- Prefer a `pipeline.yml` variable to SQL edits; keep SQL edits small and update the asset description.
- After each change: `bruin validate <pipeline-folder>`, show the diff, record it.

## 9. First run, bounded

Agree and state back, then `bruin run --environment <env> --start-date <from> --end-date <to> <pipeline-folder>`:

- **Environment:** `bruin environments list`; creating one needs approval.
- **Window:** a local run defaults to yesterday only. Say the expected scan.
- **README first-load steps:** if one is `--full-refresh`, name what it replaces before asking.

## 10. Reconcile with the user

Compare one number from the source's own dashboard.

- **Differs only by a recorded decision:** note it in `decisions.md`.
- **Differs unexplained:** stop; investigate before anyone uses the reports.

## 11. Hand off

Report template, warehouse, environment, window, unconfirmed decisions, what is scheduled (nothing unless asked), and what to connect next. Then follow `analysis.md`.
