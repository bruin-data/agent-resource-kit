# Setting up a template with the user

> **Upstream documentation wins.** Where this file disagrees with the [Bruin
> docs](https://getbruin.com/docs/bruin/overview.html) or `bruin <command>
> --help`, upstream is right and this file is stale. Written against Bruin CLI
> `v0.11.765`, checked 2026-10-01.

Every skill in the startup data kit carries an identical copy of this file.
The skill's own `SKILL.md` says which templates fit its domain and what tends to
matter there; this file is the process. Work through it in order.

## Working with the user

This is a conversation, not a script. The point of a maintained template is
that the modelling is done; the point of this process is that it ends up
modelling *this* startup, not a generic one.

- **Check before acting.** Most users have done some of this already, and
  redoing a step is how a working setup gets broken. Say what you checked and
  what you found.
- **Ask before every write.** Installing, initialising, editing configuration,
  changing a model, running a pipeline: say exactly what will change and wait
  for a yes. Show diffs.
- **Ask a few questions at a time, each with the default.** For every choice,
  say what the template does today, what the alternative would change, and why
  it matters. "Keep the default" should be an easy answer.
- **Explain the term, not just the question.** Many founders are not data
  people. "MRR counted at month end" means nothing until you say what it does
  to a mid-month signup.
- **Do not guess an answer.** If the user does not know, propose the default
  and record it as unconfirmed. A choice the user did not make should not read
  as though they did.
- **When only the user can do a step**, give them the exact steps and wait
  until they say it is done.
- **Write the answers down** as you go, in a `decisions.md` beside the
  pipeline's `pipeline.yml`: each choice, what was picked, whether the user
  confirmed it or it is still the template's default, and the date. The next
  agent, and the user in six months, will need it.

## 1. Bruin is installed

```bash
bruin version
```

- **Installed and current:** move on.
- **Installed, but `Latest` is newer than `Current`:** offer `bruin upgrade`.
  Do not run it unasked.
- **Not installed:** ask, then run
  `curl -LsSf https://getbruin.com/install/cli | sh` and check `bruin version`
  again. On Windows, or if the install fails, read
  `getting-started/introduction/installation` rather than guessing.

## 2. The Bruin MCP server is connected

Check whether you already have the `bruin_get_docs_tree` and
`bruin_get_doc_content` tools. If you do, move on.

If not, register it, because the rest of this skill reads Bruin's docs through
it. Until then, read the same pages at
`https://getbruin.com/docs/bruin/<path>.html`; the setup page is
`getting-started/bruin-mcp`.

- **If your host lets you change its MCP configuration**, show the exact
  command or snippet from that page, say which file it changes and whether that
  affects only this project or every project, and run it only after the user
  approves. For Claude Code the page gives `claude mcp add bruin -- bruin mcp`.
- **If you cannot**, walk the user through it: the snippet for their host, where
  it goes, and that the host usually needs a restart or reload before the tools
  appear.

The local server serves Bruin's documentation only. Bruin Cloud MCP is separate
(`cloud/mcp-setup`) and only worth setting up if the user runs Bruin Cloud.

## 3. You are inside the user's own git repository

```bash
git rev-parse --show-toplevel
```

- **Not a repository:** ask which folder the project should live in, then
  `git init` there. Without a repository, `bruin init` creates a `bruin/`
  wrapper folder and initialises git inside that instead.
- **A repository:** confirm it is the user's project. Never scaffold inside a
  clone of a public catalogue such as this one, or inside another Bruin
  project. A `.bruin.yml` higher up the tree gets picked up by mistake.
- **A Bruin project already exists here** (a `.bruin.yml`, a `pipeline.yml`):
  ask whether to add to it or start fresh. Adding a template to an existing
  pipeline uses `bruin init <template> <pipeline-folder> --merge`; read
  `commands/init` first, because it leaves `pipeline.yml` alone.

## 4. Confirm the warehouse

Ask which database or warehouse the data should land in. Do not pick for them.
The destination decides which templates exist at all, so ask before choosing a
template.

- **They already have one:** use it. Keep the boundary they already run.
- **They have none:** say which destinations the templates for this domain
  support (`bruin init --help` lists every template; the destination is usually
  in the name), and what each costs them in setup. Some templates run on local
  DuckDB with nothing to provision.
- **No template supports their warehouse:** say so plainly. Offer the closest
  template on another destination, or ingestion alone with the modelling left to
  build. Do not improvise a template.

## 5. Choose the template

Use the domain's `SKILL.md` for which templates to consider and their caveats.
Then confirm against the live list, because templates are added and renamed:

1. `bruin init --help` for the current names. Keep the ones that match the
   user's source and the warehouse confirmed in step 4.
2. Read each candidate's README before recommending it:
   `getting-started/templates-docs/<name>-README`. Some templates have none; say
   so and read the `README.md` it scaffolds instead.
3. Tell the user what each candidate builds, what it needs, and what it does
   not cover. Let them choose.

Then `bruin init <template>`, after they agree. Some templates, such as
`ecommerce`, open an interactive wizard and fail without a terminal; give the
user the command to run themselves, and read what it wrote afterwards. If nothing fits, say so. Ingesting a source with no template means
building the modelling yourself, which is a project; agree that with the user
before starting it. Some questions need no pipeline at all; if so, say that
too, rather than building one.

## 6. Credentials into `.bruin.yml`

`bruin init` writes a `.bruin.yml` with placeholder connections. The template's README and that file say which connections it needs.

**Never ask for a credential in chat or pass one as a command argument.** If the
user pastes one, tell them not to send it and to rotate it, because it now sits
in the transcript.

For each connection:

1. **Read what it needs.** `ingestion/<source>` for a source and
   `platforms/<warehouse>` for a destination list the required fields and link
   to the provider's own instructions.
2. **Walk the user through getting it.** Where to click at the provider, and the
   smallest scope that works: a read-only or restricted key, a service account
   with read access, never an admin or live secret key when a narrower one
   exists. A read-only credential is a control; a promise in a file is not.
3. **Keep the value out of the file.** The user stores the secret in an
   environment variable (a gitignored `.env` or `.envrc`, or their secret
   manager) and you write `${VAR_NAME}` into `.bruin.yml` (`secrets/bruinyml`).
   Or the user runs `bruin connections add` with no flags and answers its
   prompts; its flag mode puts the secret on the command line.
4. **Test it.** `bruin connections test --name <connection>`. Report the result,
   never the value.

Then confirm `.bruin.yml` is ignored: `git check-ignore .bruin.yml`. If it is
not, stop and fix that before anything else is committed.

If the user runs Bruin Cloud, the same rule holds: `bruin cloud login`, or an
exported `BRUIN_CLOUD_API_KEY`, never `--api-key` on the command line.
`bruin auth status` shows which one is active without printing it.

## 7. Work out what to ask

> **The questions come from the template, not from a list.** Templates change:
> variables are added, defaults move, reports appear and disappear. Do not work
> from a remembered or hard-coded set of questions, including any in these
> files. Read the template as it is today, list every choice it makes on the
> user's behalf, and decide which ones this user needs to confirm.

Where templates make choices:

- **The README:** configuration sections, metric policy, first-run and
  backfill steps, stated limitations.
- **`pipeline.yml`:** variables and their defaults, schedule, start date.
- **The assets:** descriptions, filters and `WHERE` clauses (statuses,
  currencies, test accounts), materialisation, column checks.
- **The report assets:** what each metric includes and excludes.

Then filter. Use what you know about the business, and ask what you do not: a
question about annual plans only matters if they sell annual plans. The domain's
`SKILL.md` lists the areas that usually matter there. Treat it as a lens for
spotting choices, not as the questions to ask.

Group what is left by topic, lead with the ones that change the headline
numbers, and ask. Add any business context the template needs but cannot infer,
such as test or internal accounts to exclude, or how much history matters.

## 8. Customise

Change the template to match the answers, one topic at a time.

- **Prefer configuration to code.** A variable in `pipeline.yml` survives a
  template update; an edited `WHERE` clause has to be carried forward by hand.
- **When SQL has to change,** keep the edit small, and update the asset's
  description to state the convention it now follows.
- **After each change,** run `bruin validate <pipeline-folder>`, show the diff,
  and record the decision in `decisions.md`.

## 9. First run, bounded

Before running, agree three things with the user and state them back:

- **The environment.** `bruin environments list`. Most templates create only
  `default`; creating or cloning another (`commands/environments`) is a change
  that needs approval.
- **The window.** `--start-date` and `--end-date`; a local run defaults to
  yesterday only. Say the expected scan.
- **The template's own first-load steps** from its README. If one is
  `--full-refresh`, name what it replaces before asking.

```bash
bruin run --environment <env> --start-date <from> --end-date <to> <pipeline-folder>
```

## 10. Check it against the source, together

A pipeline that ran and a pipeline that loaded the right data are different
claims. Pick one number the user can see in the source's own dashboard (last
month's revenue, active subscriptions, sessions) and reconcile it with them.

- **The numbers match, or differ only because of a recorded decision:** say so,
  and note the explanation in `decisions.md`.
- **They differ and you cannot say why:** stop. Investigate before anyone uses
  the reports.

## 11. Hand off

Tell the user, briefly:

- the template, warehouse, environment and window that ran;
- each decision, and which ones are still unconfirmed defaults;
- what is scheduled (nothing, unless they asked for it);
- what to connect next, if a question they care about needs a second domain.

From here, questions about the data follow the domain's `analysis.md`.
