# attio-cli

A small command-line tool and Python client for the
[Attio](https://attio.com) CRM API v2. It reads records, list entries and
schema, and — behind an explicit confirmation flag — creates, updates and
deletes them.

> **Example code, provided as-is.** This is not part of the Bruin platform and
> is not a supported Bruin product. It is a sample you configure, review and run
> yourself with your own credentials. No support agreement or SLA covers it. See
> the repository [LICENSE](../../../LICENSE) for the warranty disclaimer.

> **Upstream documentation wins.** Where anything here disagrees with
> [Attio's API documentation](https://docs.attio.com/), Attio is right and this
> file is stale. Written against the Attio REST API v2 as documented on
> 2026-09-29. Endpoint shapes came from that documentation; they have not been
> re-verified against a live workspace since. Checked 2026-09-29.

## Install

Python 3.9 or newer.

```bash
cd attio-cli
pip install -r requirements.txt
python3 scripts/cli.py --help
```

`requests` is the only hard dependency. `PyYAML` is needed only if you use a
YAML config file.

## Get an API key

In Attio: **Workspace settings → Developers → Create an access token** (an
integration's access token, not a user password). Copy it once; Attio will not
show it again.

Grant the narrowest scopes that do the job. Roughly, as of writing — confirm
against the scope list Attio shows you:

| What you want to run | Scopes |
|---|---|
| `objects`, `attrs` | object configuration, read |
| `lists`, `list-attrs` | list configuration, read |
| `search`, `query`, `get` | record permission, read |
| `entries` | list entry, read |
| `create`, `update`, `upsert`, `delete` | record permission, read-write |
| `update-entry`, `add-to-list`, `delete-entry` | list entry, read-write |

**If you only need to read, issue a read-only token.** That is the control that
actually holds. The `--yes` gate in this tool is a seatbelt, not a permission
system: a read-only token makes an accidental write impossible.

## Set the environment variable

The key is read from `ATTIO_API_KEY` and from nowhere else. There is no flag and
no config key for it, deliberately: a flag would land in your shell history and
in the process list.

```bash
export ATTIO_API_KEY='...'          # current shell only
```

For something persistent, use a file your shell loads and git ignores:

- [direnv](https://direnv.net): put `export ATTIO_API_KEY=...` in `.envrc`,
  run `direnv allow`.
- A `.env` loaded by your shell or `dotenv`.
- Your password manager's CLI, e.g. `export ATTIO_API_KEY=$(op read ...)`.

Add `.env` and `.envrc` to `.gitignore` **before** you write the key into them,
and never commit either. If a key does get committed or pasted into a chat,
revoke it in Attio and issue a new one; you cannot un-share it any other way.

## Configure

Optional, and only about *your* workspace's schema. Attio has no standard set of
objects, attributes or lists, so nothing is hardcoded here.

```bash
cp config.example.yml attio-cli.yml
python3 scripts/cli.py objects        # find your real slugs
python3 scripts/cli.py attrs companies
```

`attio-cli.yml` maps short aliases onto slugs, sets which attribute `search`
matches on, and picks the attributes shown by `--format table`. The CLI looks
for it via `--config PATH`, `$ATTIO_CLI_CONFIG`, or in the working directory.
Without a config file, whatever you type is used as the slug directly.

No credential belongs in this file.

## Commands

Read:

```bash
python3 scripts/cli.py objects
python3 scripts/cli.py attrs companies
python3 scripts/cli.py lists
python3 scripts/cli.py list-attrs <list>
python3 scripts/cli.py search companies "acme" --limit 5
python3 scripts/cli.py query companies -f '{"name":{"$contains":"acme"}}'
python3 scripts/cli.py query companies -f '<filter>' --all --max 500
python3 scripts/cli.py get companies <record-id>
python3 scripts/cli.py entries <list> --limit 20
```

Write — each prints the change and stops unless `--yes` is added:

```bash
python3 scripts/cli.py create companies '{"name":"Acme"}'
python3 scripts/cli.py update companies <record-id> '{"industry":"Software"}'
python3 scripts/cli.py upsert people email_addresses '{"email_addresses":["a@b.com"]}'
python3 scripts/cli.py delete companies <record-id>
python3 scripts/cli.py update-entry <list> <entry-id> '{"stage":"Won"}'
python3 scripts/cli.py add-to-list <list> companies <record-id> -v '{"stage":"Lead"}'
python3 scripts/cli.py delete-entry <list> <entry-id>
```

Exit codes: `0` success, `1` error, `2` a usage error (bad arguments), `3` a write
that was not confirmed.

Using the client from Python:

```python
from scripts.attio_client import AttioClient

client = AttioClient()                       # reads ATTIO_API_KEY
for record in client.iter_records("companies", max_records=200):
    print(record["id"]["record_id"])
```

The client itself does not confirm anything. The `--yes` gate lives in the CLI,
so if you script against `AttioClient` directly, you own the guard rails.

## Limitations

- **Not a sync tool.** No caching, no retries, no rate-limit backoff. A large
  `--all` run against a big workspace will be slow and may hit Attio's rate
  limits; it will surface the HTTP error rather than retrying.
- **`search` is a substring filter**, not full-text search, and it looks at one
  attribute at a time.
- **`--format table` is a convenience.** It flattens Attio's versioned value
  objects with a best-effort heuristic and can render an unusual attribute type
  poorly. Parse `--format json`, which is what the API returned.
- **`--yes` is per command invocation.** It does not track a session, so a
  scripted loop passing `--yes` gets no protection at all.
- **`delete` is permanent.** There is no undo in Attio and none here.
- Notes, tasks, comments, threads, webhooks and workspace members are not
  covered; only objects, records, attributes, lists and list entries are.
- Endpoint behaviour was taken from Attio's documentation, not from a live run
  of every command. Check the responses you get.
