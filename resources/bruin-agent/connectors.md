# Bruin sources, destinations and templates

> **Upstream documentation wins.** Bruin adds templates and connectors faster
> than a file like this gets updated, so this one carries no catalogue. Run
> `bruin init --help` for the live template list and check the [Bruin
> docs](https://getbruin.com/docs/bruin/getting-started/templates.html) before
> relying on anything here. Written against Bruin CLI `v0.11.765`, checked
> 2026-09-30.

A **template** is a whole pipeline with modelling and reports. A **connector**
only means ingestion is supported; the modelling is yours to write. Prefer a
template where one exists.

## Look it up live

- **Template names:** `bruin init --help`. `getting-started/templates` and
  `bruin_get_overview` both miss some.
- **What a template builds and needs first:**
  `getting-started/templates-docs/<name>-README`. Some, such as
  `stripe-databricks`, have no page; read the `README.md` that `bruin init`
  writes instead.
- **Sources:** `bruin_get_docs_tree`, then `ingestion/<source>`; warehouses and
  databases under `platforms/<name>`. Page names can differ from the connection
  type key (`google-ads` for `googleads`).
- **What a project already has:** `bruin connections list`, names only.
- **Connection types in Bruin Cloud:** the Cloud MCP `connection-types` tool. It
  needs a Cloud token and is not a full list of what local `bruin` can ingest.
- **ingestr internals:** the [ingestr docs](https://getbruin.com/docs/ingestr/),
  which `bruin mcp` does not serve.

## What the docs do not say

**Credential-free, for learning or a demo:** `default` (what `bruin init` uses
with no template name), `duckdb`, `duckdb-example`, `duckdb-lineage`, `chess`,
`frankfurter`, `nyc-taxi`, `variant-example`, `iceberg-sqlite-local`, `python`,
`r`, `bootstrap`, `empty`, `demo-self-heal-pipeline`, `zoomcamp`, and the
`academy-sql-*` series. None needs a credential for local use. Caveats:
`duckdb-example` and `empty` write no `.bruin.yml`, so add a local DuckDB
connection (`duckdb-default` for `duckdb-example`) first; `zoomcamp` is a
fill-in-the-TODOs tutorial whose last part deploys to BigQuery; and the
`academy-sql-*` templates add a `cloud` environment that needs
`${MOTHERDUCK_TOKEN}`. `getting-started/templates` lists only some of these.

**There is no generic `snowflake` starter.** The Snowflake templates are the
`demo-snowflake-*` pair.

## When no connector exists

In order of how much is being taken on:

1. An `ingestr` asset against a supported connector that has no full template.
2. `bruin curl` (`commands/curl`), which renders connection credentials into a
   curl call so nobody handles the secret directly. Good for a small or unusual
   API. The rendered value is in curl's argument list while it runs, so say so
   on a shared machine.
3. A Python asset for anything else.

Options 2 and 3 are provisional until they have a test fixture, documented
rate-limit behaviour, and a human review. Say so in the asset description. Do
not schedule one or base a consequential decision on it before then.
