# Answering finance and accounting questions

> **Upstream documentation wins.** Where this file disagrees with the [Bruin
> docs](https://getbruin.com/docs/bruin/overview.html), `bruin --help`, or
> Intuit's QuickBooks Online documentation, those are right and this file is
> stale. Written against Bruin CLI `v0.11.766`, checked 2026-10-01.

Read `decisions.md` beside the pipeline's `pipeline.yml` first. The Never rules
in [SKILL.md](SKILL.md) apply.

## Before answering

- Read the asset descriptions before writing SQL.
- Check freshness: the last runs (Bruin Cloud MCP or `bruin cloud runs list`), and that the period is closed; a reopened month changing is the bookkeeper's change, not a bug.
- Check the company and environment; two companies are not one business until someone says how to consolidate.
- State the basis, as-of date, currency and company, and which unloaded transaction types bear on the answer.

## Traps

- Invoiced (accrual billing, including tax) is not recognised revenue, and collected is not cash in the bank; never relabel one as another.
- Balances are open amounts at the last load, so past-date AR means rebuilding from payment lines; subtract unapplied payments, and expect QuickBooks' aging to read lower by the open credit memos.
- Measure cash from payment totals, not summed applied lines; one payment covers many invoices, and an application can be a credit.
- A deleted invoice keeps its last balance until a full refresh, and there is no void flag; check before chasing an "overdue" invoice.
- Concentration on a short window is mostly timing; report by QuickBooks ID, not name.
- Books and billing will not match: an annual plan is twelve months of MRR and one invoice, there is no shared customer key, and a synced charge added to billing is the same money twice.

## What this data cannot tell you

- Burn, runway or vendor spend: bills, expenses, payroll and bank balances are not loaded.
- Gross margin, P&L or balance sheet: use QuickBooks' own reports.
- MRR: use the billing system, in `revenue-analytics`.
- Tax owed: that is the accountant's; never answer it from this data.
