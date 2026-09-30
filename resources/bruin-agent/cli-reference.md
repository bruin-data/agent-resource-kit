# Bruin CLI: what to reach for

> **Upstream documentation wins.** Run `bruin <command> --help` for current
> flags rather than trusting this file, and prefer the [Bruin
> docs](https://getbruin.com/docs/bruin/overview.html) where they disagree with
> it. Written against Bruin CLI `v0.11.765`, checked 2026-09-29.

## By task

| Task | Command |
|---|---|
| Scaffold a project | `bruin init <template>`, `--merge` to add to an existing one, `--in-place` to skip the parent folder |
| Check before running | `bruin validate .` |
| See the SQL that will run | `bruin render <asset>` |
| Run | `bruin run --environment dev .`, add `--workers 1` for DuckDB |
| Run one asset | `bruin run <path to asset>` |
| Query | `bruin query -c <connection> -q "..."`, `-o json|csv`, `--limit` |
| Query by metric name | `bruin query --semantic-model <m> --metric <x> --dimension <d>` |
| Trace dependencies | `bruin lineage <asset>`, `--full` for indirect |
| Compare environments or sources | `bruin data-diff <a> <b>` |
| Test SQL logic | `bruin unit-test <asset or pipeline>` |
| Resumable historical load | `bruin backfill` |
| Add a connection | `bruin connections add` (interactive) |
| List connections | `bruin connections list` (metadata only, never secrets) |
| Manage environments | `bruin environments list|create|update|delete|clone` |
| Suggest descriptions and checks | `bruin ai enhance` |
| Install agent skills | `bruin ai skills all` |
| Generate a docs site | `bruin docs --open` |
| Call an API with stored credentials | `bruin curl` |
| Import existing work | `bruin import database|bq-scheduled-queries|snowflake-tasks|odi|tableau` |
| Format asset files | `bruin format` |
| Clear temp artifacts | `bruin clean` |
| Update the CLI | `bruin upgrade` |

## Flags worth knowing

- `--environment dev` on anything that touches data. Say which you used.
- `--start-date` / `--end-date` bound a run. Set `start_date` in `pipeline.yml`
  before the first run instead of discovering the cost afterwards.
- `--config-file` forces a specific `.bruin.yml` when the tree is ambiguous.
- `--secrets-backend vault|doppler|aws|azure` for external secret managers.
- `--dry-run` on `query` validates and shows estimated cost where the platform
  supports it. Use it before anything that might scan a lot.
- `--description` on `query` records why an agent ran something. Use it.

## Habits that matter

**Validate, render, then run.** `bruin validate` catches structural problems
without touching data. `bruin render` shows the SQL that will actually execute,
templating resolved. Both are free.

**Query narrow first.** Select the columns needed, filter the date range, limit
rows. State the expected scan before running anything materially larger than the
last query.

**Never print a credential.** `bruin connections list` returns metadata only.
Keep it that way in your own output too, including error messages and summaries.

**Stop and ask** before `--full-refresh`, a backfill, anything against `prod`,
any write to a source system, any outbound message, and any new network
destination.

## Assets

| Type | Use |
|---|---|
| `ingestr` | Source to destination, with incremental strategies, schema contracts, partitioning |
| `<platform>.sql` | Transformations. Metadata lives between `/* @bruin` and `@bruin */` |
| `<platform>.seed` | Load a CSV. Good for reference data and fixtures |
| `python` | Managed dependencies, can return dataframes |
| `r` | R transformations |

Asset metadata carries column descriptions, primary keys, quality checks, tags
and sensitive-field markers. Quality checks run as part of `bruin run`, so a
check is how you make a modelling assumption fail loudly instead of silently.

## Semantic layer

Models live in `semantic/` next to `.bruin.yml`, defining reusable metrics,
dimensions, segments and joins in version-controlled YAML. Query by name rather
than reconstructing business logic in SQL each time:

```bash
bruin query -c <connection> --pipeline <path> --semantic-model <model> \
  --metric mrr --dimension month:month --sort month:desc
```

`bruin ai skills bruin-semantic-layer` installs detailed guidance for building
these. Install it before creating or editing semantic models.

## Reference

- Overview: https://getbruin.com/docs/bruin/overview.html
- Ingestr assets: https://getbruin.com/docs/bruin/assets/ingestr.html
- Quality checks: https://getbruin.com/docs/bruin/quality/overview.html
- Semantic layer: https://getbruin.com/docs/bruin/core-concepts/semantic-layer.html
- Secrets: https://getbruin.com/docs/bruin/core-concepts/secrets.html
