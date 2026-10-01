# Revenue metric decisions

> **Upstream documentation wins.** This file describes choices, not vendor
> behaviour. For how a specific field actually behaves, your billing provider's
> documentation is the source of truth, and their own reporting is what you
> reconcile against. For what a Bruin template chose, its README is. Where this
> file disagrees with any of them, they are right. Template defaults below are
> from the Bruin CLI `v0.11.765` template READMEs, checked 2026-09-30.

Ten choices that change the MRR number. None of them have a single correct
answer. Templates ship defaults for several: read the metric policy in the
template's README (`bruin_get_doc_content('getting-started/templates-docs/<name>-README')`)
and confirm each default with the user. A default nobody confirmed is still a
silent pick, and a model that picks silently is teaching the user a hard
question is already settled.

Read this when building or reviewing a revenue model. For a single question,
surface only the decisions that actually bear on it.

## 1. Annual and multi-year plans

**What it changes:** the largest single source of overstated MRR.

Divide the committed amount across the term. A `$12,000` annual plan is `$1,000`
of MRR for twelve months, not `$12,000` in the month it was billed. Booking the
full amount on the invoice date makes one enterprise deal look like a step change
in recurring revenue.

**Ask:** does the model normalise every billing interval to a monthly amount?
Check what it does with quarterly and two-year terms too.

## 2. Multiple currencies

**What it changes:** the number moves when exchange rates move, even if nothing
about the business changed.

Three defensible options: convert at a fixed rate set once, convert at the rate
on the day, or report per currency and never add them up. All are fine. Mixing
them, or not saying which is in use, is not.

**Ask:** which one, and is the rate and its date recorded next to the number?

**On a template:** the Stripe and Chargebee templates report per currency and
apply no FX. Summing their output across currencies is the user's choice to
make, not the template's.

## 3. Usage and metered billing

**What it changes:** whether "recurring" means anything.

Usage revenue is not recurring in the same sense as a subscription. A customer
who spent `$4,000` last month may spend `$200` this month. Folding it into MRR
makes the metric volatile and undermines the reason to track MRR at all.

**Ask:** report it as a separate line, or define an explicit smoothing window
such as a trailing three-month average, and label it as smoothed.

**On a template:** check what its README chose. `stripe-bigquery` leaves metered
prices out of MRR entirely.

## 4. Trials

**What it changes:** the customer count, and sometimes the churn rate.

A trialling customer usually has a subscription object and no revenue. Counting
them as a customer inflates the count and depresses ARPA. Excluding them hides
the top of the funnel. Counting them as churn when the trial lapses inflates
churn badly.

**Ask:** are they customers, and does a lapsed trial count as churn?

**On a template:** check what its README chose. `chargebee-bigquery` leaves
trials out unless `in_trial` is added to `mrr_active_statuses`.

## 5. Paused and past-due subscriptions

**What it changes:** the gap between MRR and cash, and when churn is recognised.

Stripe keeps these in `past_due`, `unpaid` or `paused`. They are still active
subscriptions carrying MRR while collecting nothing. Counting them indefinitely
means MRR drifts above reality; dropping them immediately means a failed card
looks like churn.

**Ask:** after how many days or failed attempts does a non-paying subscription
stop counting? Pick a number and write it down.

**On a template:** check what its README chose. `stripe-bigquery` counts active
and past-due subscriptions. `chargebee-bigquery` counts the statuses in
`mrr_active_statuses`, by default `active` and `non_renewing`.

## 6. Discounts and coupons

**What it changes:** usually a few percent, permanently.

This file recommends MRR net of discount. A customer on a `$199` plan with a 20%
coupon is `$159.20` of MRR. Reporting list price overstates revenue and makes
the model disagree with cash for a reason nobody can find later.

**Ask:** which side of the discount is this number on, and what happens when the
coupon expires?

**On a template:** check what its README chose. `stripe-bigquery` reports gross
list-price MRR with discounts not applied, the opposite of the recommendation
above. Say so next to any number from it.

## 7. Taxes

**What it changes:** a small, persistent, maddening gap between MRR and invoices.

MRR should exclude tax. Invoice totals include it. When someone says "MRR does
not match what Stripe shows me", this is often why.

**Ask:** is the model reading a pre-tax subtotal or an invoice total?

## 8. Proration

**What it changes:** the relationship between invoices and MRR, mid-cycle.

A plan change mid-cycle generates a prorated invoice matching no monthly amount.
It is real cash and it is not a change in recurring revenue.

**Ask:** does proration affect MRR, or only the cash view? Most models should say
cash only, and should say so out loud.

## 9. Refunds and disputes

**What it changes:** which month takes the hit.

A refund issued in March for a January invoice can reduce March or January. Both
are defensible; restating a closed month is not always welcome.

**Ask:** issue month or original month, and are disputes and chargebacks handled
the same way?

## 10. MRR timing

**What it changes:** every number in the report, subtly.

Three conventions:

| Convention | Behaviour |
|---|---|
| **Observed at month start** | A subscription counts if it was live on the 1st. Stops a mid-month plan change counting the old and new plan in the same month. A mid-month signup first appears the following month. |
| **Observed at month end** | Mirror image. Flatters new business in its first month. |
| **Daily average** | Most accurate, hardest to reconcile against anything, and harder to explain. |

All three are defensible. Only one should appear in the reports.

**Ask:** which one, and is it stated next to the number?

**On a template:** check what its README chose. The Stripe and Chargebee
templates both report MRR observed at month end.

## Using this list

When reviewing an existing model, go through all ten and record the answer next
to each metric definition. The recording matters as much as the choice: the cost
of an undocumented convention is not that it is wrong, it is that six months
later nobody can say what the number means.

When answering a single question, surface only the decisions that bear on it. A
question about churn count does not need the currency policy.
