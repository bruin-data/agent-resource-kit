# Bruin sources, destinations and templates

> **Upstream documentation wins.** This list goes out of date by design: Bruin
> adds templates and connectors faster than a file like this gets updated. Run
> `bruin init --help` for the live template list and check the [Bruin
> docs](https://getbruin.com/docs/bruin/getting-started/templates.html) before
> relying on an entry. Written against Bruin CLI `v0.11.765`, checked
> 2026-09-23.

Grouped by what someone is trying to answer. `bruin connections list` shows
what a project already has configured; the MCP `connection-types` tool lists
every type and its required fields.

A connector and a template are different things. A **template** is a whole
pipeline with modelling and reports. A **connector** only means ingestion is
supported; the modelling is yours to write. Prefer a template where one exists.

## Templates

| Template | Destination | Covers |
|---|---|---|
| `stripe-bigquery` | BigQuery | Stripe billing: 19 assets across raw, stage, reports. MRR by customer, MRR movements, subscription KPIs, invoice billings, daily snapshots, dashboard |
| `stripe-databricks` | Databricks | Stripe billing |
| `chargebee-bigquery` | BigQuery | Chargebee billing |
| `shopify-duckdb` | DuckDB | Ecommerce, local |
| `shopify-bigquery` | BigQuery | Ecommerce |
| `shopify-clickhouse` | ClickHouse | Ecommerce |
| `ecommerce` | Selectable | Composes Shopify, Stripe, Klaviyo or HubSpot, advertising, and GA4 or Mixpanel into raw, staging, and revenue, customer, product, marketing and KPI reports |
| `posthog-bigquery` | BigQuery | Product analytics: account-level engagement and feature-adoption reports, dashboard |
| `firebase` | BigQuery | Mobile and app analytics |
| `google-web-analytics` | BigQuery | GA4 plus Search Console exports into staging models and nine analytical reports |
| `gsheet-duckdb`, `gsheet-bigquery` | DuckDB, BigQuery | Spreadsheets as the system of record |
| `notion` | | Workspace content |
| `gorgias` | | Customer support |
| `ai-coding-usage` | DuckDB | Normalises Claude Code and Cursor usage |
| `migration-fivetran` | | Review-gated Fivetran import |
| `demo-snowflake-sales-analytics` | Snowflake | Bronze, silver, gold retail modelling |
| `demo-snowflake-salesforce` | Snowflake | Relationship and marketing analytics |
| `demo-payments-clickhouse` | ClickHouse | CDC and rollups |
| `bronze-silver-postgres` | Postgres | Curated silver models with quality checks |

**Credential-free, for learning or a demo:** `duckdb`, `duckdb-example`,
`duckdb-lineage`, `chess`, `frankfurter`, `nyc-taxi`, `iceberg-sqlite-local`,
`python`, `r`, `bootstrap`, `empty`, `demo-self-heal-pipeline`, and the
`academy-sql-*` series.

**Warehouse starters:** `bigquery`, `snowflake`, `databricks`, `clickhouse`,
`redshift`, `athena`, `postgres`-based, plus five `iceberg-*` catalog and
storage combinations.

## Sources by domain

### Billing, payments and finance

`stripe`, `chargebee`, `paddle`, `recurly`, `revenuecat`, `adapty`, `square`,
`fastspring`, `solidgate`, `twocheckout`, `primer`, `payrails`, `wise`,
`fundraiseup`, `fakturoid`, `abraflexi`, `deel`, `personio`, `bamboohr`

FX rates: `frankfurter` (no credentials), `exchangeratesapi`

### Advertising and attribution

`googleads`, `facebookads`, `tiktokads`, `linkedinads`, `appleads`,
`snapchatads`, `pinterest`, `reddit_ads`, `applovin`, `applovinmax`, `sklik`

Mobile attribution: `adjust`, `appsflyer`

### CRM and lifecycle

`hubspot`, `salesforce`, `pipedrive`, `attio`, `twenty`, `klaviyo`, `mailchimp`,
`braze`, `customerio`, `sendgrid`, `intercom`, `zendesk`, `freshdesk`,
`gorgias`, `trello`, `monday`, `asana`, `clickup`, `linear`, `jira`, `notion`

### Product analytics and feedback

`posthog`, `mixpanel`, `amplitude`, `adapty`, `revenuecat`, `satismeter`,
`surveymonkey`, `typeform`, `trustpilot`, `g2`

### Web analytics and search

`googleanalytics` (GA4), `gsc` (Google Search Console), `cloudflare_radar`

### Warehouses and databases

`bigquery` via `google_cloud_platform`, `snowflake`, `databricks`, `clickhouse`,
`redshift`, `athena`, `postgres`, `mysql`, `mssql`, `oracle`, `db2`, `hana`,
`vertica`, `synapse`, `fabric`, `starrocks`, `motherduck`, `planetscale_mysql`,
`vitess`, `spanner`, `mongo`, `mongo_atlas`, `couchbase`, `dynamodb`,
`elasticsearch`, `influxdb`

### Files, storage and streams

`s3`, `gcs`, `adls`, `onelake`, `sftp`, `sharepoint`, `google_sheets`,
`smartsheet`, `airtable`, `kafka`, `kinesis`, `rabbitmq`

### Engineering and AI usage

`github`, `gitlab`, `anthropic`, `cursor`, `okta`

### Messaging destinations

`slack`, `ms_teams`, `discord` (webhook based)

## When no connector exists

In order of how much is being taken on:

1. An `ingestr` asset against a supported connector that has no full template.
2. `bruin curl`, which renders connection credentials into an HTTP request so
   nobody handles the secret directly. Good for a small or unusual API.
3. A Python asset for anything else.

Options 2 and 3 are provisional until they have a test fixture, documented
rate-limit behaviour, and a human review. Say so in the asset description. Do
not schedule one or base a consequential decision on it before then.

## Reference

- Templates: https://getbruin.com/docs/bruin/getting-started/templates.html
- Ingestr sources: https://getbruin.com/docs/ingestr/
- Connections: https://getbruin.com/docs/bruin/commands/connections.html
- Ingestr assets: https://getbruin.com/docs/bruin/assets/ingestr.html
