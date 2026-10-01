---
name: finance-accounting
description: Use when a startup wants QuickBooks Online data set up or answered. Sets up the quickbooks-bigquery template and answers accounts receivable, aging, invoiced versus collected, customer concentration and vendor questions, and how the books differ from MRR.
---

# Finance and accounting

**Status:** experimental · **Risk:** approval-required

> **Upstream documentation wins.** Where this file disagrees with the [Bruin
> docs](https://getbruin.com/docs/bruin/overview.html), `bruin --help`, or
> Intuit's QuickBooks Online documentation, those are right and this file is
> stale. Written against Bruin CLI `v0.11.766`, checked 2026-10-01.

Sets up the QuickBooks template to how this company keeps its books and answers
AR, collections and concentration questions from it. It exists to prevent a
figure that looks like the books but was summed from a partial copy: the wrong
company, mixed currencies, deleted transactions or an unclosed month.

## Set up

Follow [workflow.md](workflow.md).

> **Important: do not ask a fixed list of questions.** Read the template as it
> is today and work out which of its choices this user needs to confirm.
> Templates change, so the questions change with them.

**Templates:** `quickbooks-bigquery`; confirm with `bruin init --help`. Not on
BigQuery: read `ingestion/quickbooks`; the modelling is theirs to build. No
Xero or NetSuite connector existed when written; check the docs tree.

**Watch for:**

- Ingestion only, no reports: every AR or concentration figure is SQL you write.
- Bills, expenses, credit memos, sales receipts and journal entries are not loaded: no P&L, balance sheet, burn or vendor spend.
- Deletes are not picked up and inactive records still read active; only a full-window `--full-refresh` catches them.
- Invoices are not MRR; with a billing system, MRR belongs to `revenue-analytics`.

**Usually needs the user's input:**

- Which company: the realm, production or sandbox (sandbox numbers are test data), and whether several companies must stay separate.
- How revenue reaches the books: QuickBooks invoices, a billing sync posting invoices or sales receipts, or journal entries; only invoices load.
- Cash or accrual, and which months the bookkeeper has closed.
- Home currency, multi-currency and the FX policy; amounts are in transaction currency only.
- Whether figures are before or after tax; invoice totals include it.
- Customer grain (sub-customers are separate rows), and aging by due or invoice date, with buckets.
- Deletes or voids, how often to full-refresh, and test, internal or intercompany customers to exclude.

**Reconcile against:** QuickBooks' A/R aging summary against open invoice
balances less unapplied payments, and one closed month's invoice total against
its invoice list, on the same basis and as-of date.

## Answer questions

Read [analysis.md](analysis.md).

## Never

- Ask for or print a credential; write, run, backfill, `--full-refresh` or
  touch production without a yes; put personal data in output.
- Write to QuickBooks, whatever the OAuth scope allows, or `--full-refresh` a window narrower than the README's.
- Sum amounts across currencies without a recorded FX policy.
- Present a figure as the books, a financial statement or tax advice.

## Unverified

- Whether balances update when a new transaction posts; compare one bank account with QuickBooks after a busy day.
- Whether Intuit offers a narrower scope than `com.intuit.quickbooks.accounting`; until its scope docs say so, treat the token as able to write.
- Whether a credit memo application appears as a zero-amount payment; read `LinkedTxn` types on zero-total payments before cohorting collections.
