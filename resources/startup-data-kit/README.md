# Startup data kit

> **Upstream documentation wins.** Where a skill here disagrees with the tool's
> own documentation or its `--help` output, upstream is right and the file here
> is stale. Each skill states the version and date it was written against.
> Checked 2026-10-01.

One skill per domain: an agent sets up a maintained Bruin template with the
user, customises it, then answers questions from it. Take the folders you need.

| Resource | Domain | Example sources |
|---|---|---|
| [`revenue-analytics`](revenue-analytics/) | Finance and billing | Stripe, Chargebee, Paddle, RevenueCat, Shopify |
| [`marketing-analytics`](marketing-analytics/) | Advertising, lifecycle, CRM | Google Ads, Meta, TikTok, LinkedIn, HubSpot, Klaviyo, Salesforce |
| [`product-analytics`](product-analytics/) | Usage and activation | PostHog, Mixpanel, Amplitude, Firebase |
| [`web-analytics`](web-analytics/) | Traffic and acquisition | GA4, Search Console |
| [`ai-search-visibility`](ai-search-visibility/) | SEO, GEO, AEO | Search Console, server logs, third-party sampling tools |
| [`finance-accounting`](finance-accounting/) | Bookkeeping and accounting | QuickBooks Online |
| [`support-analytics`](support-analytics/) | Customer support | Gorgias, Zendesk, Intercom, Freshdesk |
| [`ai-coding-spend`](ai-coding-spend/) | AI coding tools | Claude Code, Cursor |
| [`sheets-and-notion`](sheets-and-notion/) | Hand-maintained data | Google Sheets, Notion |

Sources are examples; read `ingestion/<source>` before promising one. Get one
domain reconciling against its source before adding a second.

## How each skill works

Every folder holds these three files:

| File | What it is |
|---|---|
| `SKILL.md` | What is specific to the domain: which templates to consider, what usually needs the user's input, what to reconcile against |
| `workflow.md` | The shared setup process, from installing Bruin to reconciling the first run |
| `analysis.md` | How to answer questions once the pipeline exists |

`ai-coding-spend` also carries a [`sample-data/`](ai-coding-spend/sample-data/)
folder: fake Claude Code and Cursor usage that runs its template on DuckDB with
no credentials.

`workflow.md` is identical in every folder, so a skill copied alone still works.
`tests/check.py` fails if the copies drift; edit one and copy it to the rest.

The skills carry no fixed list of questions: the agent reads the template as it
is today and works out what this user must decide. Answers go in `decisions.md`
beside the pipeline.

## Questions that span domains

Many useful questions need data from more than one domain:

| Question | Domains |
|---|---|
| Which customers are about to churn | revenue + product |
| Which channels bring customers who stay | marketing + revenue |
| Where users drop out of the funnel | web + product + revenue |
| Whether content investment pays back | ai-search-visibility + web + revenue |
| Which customers cost more to support than they pay | support + revenue |
| Actuals against the plan | sheets-and-notion + revenue or finance |

Each needs a stable identifier shared by the sources, such as a customer ID or
email address. Where none exists, building that mapping comes first, and the
skills say so instead of answering from one source alone.
