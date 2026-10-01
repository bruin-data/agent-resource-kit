---
name: attio-cli
description: Use when reading or changing live Attio CRM data from a terminal - searching companies, people or deals, discovering object, attribute and list slugs, reading list entries, or creating, updating or deleting records. Reads run freely; every write is gated behind an explicit --yes.
---

# Attio CLI

**Status:** experimental · **Risk:** approval-required

> **Upstream documentation wins.** Where this file disagrees with
> [Attio's API documentation](https://docs.attio.com/), Attio is right and this
> file is stale. Written against the Attio REST API v2 as documented at
> docs.attio.com, checked 2026-09-29. The endpoint shapes in `scripts/` were
> taken from that documentation and have not been re-run against a live
> workspace since. Verify any endpoint, filter operator or attribute type before
> relying on it, and tell the user when you find a difference.

Sample scripts in `scripts/` wrap the Attio API. Use them for questions about
the *current* state of a CRM. If the user has a warehouse copy of Attio, prefer
the warehouse for history, trends and aggregates, and this for what is true now.

## Setup, once per project

1. `pip install -r requirements.txt`
2. The key comes from the `ATTIO_API_KEY` environment variable only. **Never ask
   the user to paste it into the chat and never put it in a command.** Tell them
   to create an access token in Attio (Workspace settings, Developers), grant it
   only the scopes they need, and export it themselves:
   `export ATTIO_API_KEY=...` in a gitignored `.env` / `.envrc` they load.
3. If the command exits saying `ATTIO_API_KEY is not set`, relay that message.
   Do not work around it.

## Discover the schema before doing anything else

There is no standard Attio schema. Objects, attributes and lists are per
workspace, and even the built-in ones get renamed. Never guess a slug, and never
carry one over from another workspace.

```bash
python3 scripts/cli.py objects              # object slugs
python3 scripts/cli.py attrs companies      # attribute slugs, types, titles
python3 scripts/cli.py lists                # list slugs
python3 scripts/cli.py list-attrs <list>    # attribute slugs on a list
```

Optional: `config.example.yml` maps short aliases onto this workspace's slugs
and sets the attribute `search` matches on. Copy it to `attio-cli.yml` once the
real slugs are known. Without it, every name you type is sent as the slug.

## Read

```bash
python3 scripts/cli.py search companies "acme" --limit 5
python3 scripts/cli.py query companies -f '{"name":{"$contains":"acme"}}'
python3 scripts/cli.py query deals -f '<filter>' --all --max 500
python3 scripts/cli.py get companies <record-id>
python3 scripts/cli.py entries <list> -f '<filter>' --limit 20
```

`search` is a `$contains` filter on one attribute, not full-text search; pass
`--attribute` when `name` is wrong for that object. Output is JSON by default;
`--format table` prints a compact line per record and is for eyeballing only,
never for parsing. Filter syntax is attribute-level operators (`$eq`, `$neq`,
`$contains`, `$gt`, `$gte`, `$lt`, `$lte`) combined with `$and` / `$or`; check
the [filtering documentation](https://docs.attio.com/rest-api/how-to/filtering-and-sorting)
for which operators a given attribute type accepts.

## Write, only with the user's approval

`create`, `update`, `upsert`, `delete`, `update-entry`, `add-to-list` and
`delete-entry` change a CRM that people run their week from. Each one prints the
exact change and exits without doing anything unless `--yes` is passed (`update`
and `delete` also print the current values first).

Run the command **without** `--yes`, show the user that output, and get their
agreement before re-running it with `--yes`. Do this per change, not once for a
batch. For anything touching more than a handful of records, say how many are
affected and get agreement on the whole set first.

`delete` is irreversible. `upsert` overwrites an existing record when the
matching attribute hits, so treat it as an update.

Attio's response is JSON; report what actually came back rather than assuming
the change landed as asked.

## Never

- Never ask for, accept, print or log the API key. If the user pastes one, tell
  them not to and to rotate it.
- Never pass the key as a flag, put it in `attio-cli.yml`, or commit any file
  that contains it.
- Never invent an object, attribute or list slug. Run the discovery commands.
- Never run a write with `--yes` that the user has not seen and agreed to.
- Never bulk-edit or delete to "clean up" the CRM on your own initiative.

## Unverified

Nothing here was run against a live Attio workspace. Endpoint shapes, filter
operators and attribute types came from the documentation.

Two places where the code the port came from disagreed with current Attio docs,
both worth confirming on your first run:

- **`add-to-list` requires `parent_object`.** The original omitted it. If Attio
  rejects the call, read the create-entry docs and adjust.
- **`upsert` sends `matching_attribute` as a query parameter.** The original put
  it in the body. The client tries the query form and falls back to the body form
  once on HTTP 400.

Run a read command first, against one record, before trusting any write path.

## Files

| File | Purpose |
|---|---|
| `scripts/attio_client.py` | API client. Reads `ATTIO_API_KEY`, scrubs it from errors |
| `scripts/cli.py` | The command line, including the `--yes` write gate |
| `config.example.yml` | Optional alias-to-slug map for one workspace |
| `requirements.txt` | `requests`, plus `PyYAML` for a YAML config |
| `README.md` | Human setup notes and limitations |
