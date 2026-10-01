---
name: sheets-and-notion
description: Use when a startup wants hand-kept data from Google Sheets or Notion set up or answered. Sets up the gsheet-bigquery, gsheet-duckdb or notion template and answers questions joining plans, targets, mappings and OKRs to other domains, such as targets against MRR.
---

# Sheets and Notion

**Status:** experimental · **Risk:** approval-required

> **Upstream documentation wins.** Where this file disagrees with the [Bruin
> docs](https://getbruin.com/docs/bruin/overview.html), `bruin --help`, or
> Google Sheets or Notion documentation, those are right and this file is
> stale. Written against Bruin CLI `v0.11.766`, checked 2026-10-01.

Loads hand-kept sheets and Notion databases and answers questions joining them
to other domains. It exists to prevent quiet breakage when people edit the
file, and a typed value being read as a measurement.

## Set up

Follow [workflow.md](workflow.md).

> **Important: do not ask a fixed list of questions.** Read the template as it
> is today and work out which of its choices this user needs to confirm.
> Templates change, so the questions change with them.

**Templates:** `gsheet-bigquery`, `gsheet-duckdb`, `notion` (to BigQuery);
confirm with `bruin init --help`. Other warehouses have no template: copy the
asset and change its destination. Airtable, Smartsheet and SharePoint: read
`ingestion/<source>`; the modelling is theirs to build.

**Watch for:**

- One raw copy per tab or database; cleaning, typing and unpivoting are models to build.
- Every load replaces the table: current state only, no history. A re-forecast overwrites the original target; deleted rows disappear.
- Google sharing is per file, not per tab: a Viewer reads every tab.
- Notion relations are IDs into other databases (load those too); people properties carry names and emails.

**Usually needs the user's input:**

- Scope: which files, tabs and databases, and which are sensitive, before opening any.
- Source of truth: system of record, or a hand copy of another system's data? Prefer the system.
- Shape and types: header row, title or totals rows, merged cells, months as columns, text dates, "TBD" in number columns.
- Drift: fail the run on a renamed column (`schema_contract: freeze`), or let it quietly go NULL (default).
- Join keys: must match the other domain's ID exactly; names are not IDs.
- Grain, calendar, currency and metric convention of whatever the targets are compared to.
- History: to keep old plans, agree an append or snapshot before the first run; `--full-refresh` then discards it.

**Reconcile against:** the file itself: data-row count and one numeric
column's total against the loaded table; for Notion, the database row count
with every view filter removed.

## Answer questions

Read [analysis.md](analysis.md).

## Never

- Ask for or print a credential; write, run, backfill, `--full-refresh` or
  touch production without a yes; put personal data in output.
- Write to the sheet or Notion: no Editor access, no Sheets destination, no fixing source values.
- Open or load a tab or database that is not in scope.
- Present a typed value as a measurement; say whose it is and as of when.

## Unverified

- How a sheet is parsed (blank rows, formulas, dates, mixed types); load a scratch tab and inspect it.
- The loaded shape of Notion properties on BigQuery; query the table's schema before modelling.
- Whether a renamed header leaves a NULL column or drops it; rename one on a scratch tab and rerun.
