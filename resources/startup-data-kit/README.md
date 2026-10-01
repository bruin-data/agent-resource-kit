# Startup data kit

> **Upstream documentation wins.** Where a skill here disagrees with the tool's
> own documentation or its `--help` output, upstream is right and the file here
> is stale. Each skill states the version and date it was written against.
> Checked 2026-10-01.

Getting a startup's data into shape and answering questions from it. Each skill
has an agent work with the user to set up a maintained Bruin template and
customise it to how the business actually works, then answer questions from
what it built. One resource per domain, because the traps are domain-specific:
what ruins a revenue number is not what ruins an attribution number.

Each folder is an independent skill. Take the ones you need.

| Resource | Domain | Example sources |
|---|---|---|
| [`revenue-analytics`](revenue-analytics/) | Finance and billing | Stripe, Chargebee, Paddle, RevenueCat, Shopify |
| [`marketing-analytics`](marketing-analytics/) | Advertising, lifecycle, CRM | Google Ads, Meta, TikTok, LinkedIn, HubSpot, Klaviyo, Salesforce |
| [`product-analytics`](product-analytics/) | Usage and activation | PostHog, Mixpanel, Amplitude, Firebase |
| [`web-analytics`](web-analytics/) | Traffic and acquisition | GA4, Search Console |
| [`ai-search-visibility`](ai-search-visibility/) | SEO, GEO, AEO | Search Console, server logs, third-party sampling tools |

The sources are examples, not the supported list. Check what Bruin can ingest
today with the local Bruin MCP server's `bruin_get_docs_tree` (the `ingestion/`
section), and read `ingestion/<source>` before promising one.

## How each skill works

Every folder holds the same three kinds of file:

| File | What it is |
|---|---|
| `SKILL.md` | What is specific to the domain: which templates to consider, what usually needs the user's input, what to reconcile against |
| `workflow.md` | The shared process: check Bruin is installed and its MCP server connected, work inside the user's git repository, confirm the warehouse, pick a template, set up credentials, then ask, customise, run and reconcile |
| `analysis.md` | How to answer questions once the pipeline exists |

`workflow.md` is identical in every folder, so a skill copied on its own still
works. `tests/check.py` fails if the copies drift apart; edit one and copy it to
the rest.

The skills do not carry a fixed list of questions. Templates change, so the
agent reads the template as it is and works out what this user needs to decide.
Answers go in a `decisions.md` beside the pipeline.

## Start here

Take the domain that answers the question you actually have. Most startups
should get one domain reconciling against its own source before adding a second.
Connecting five sources before any of them is trusted produces a dashboard
nobody believes.

## The joins are where the value is

Each domain answers useful questions alone. The ones worth the setup cross two:

| Question | Domains |
|---|---|
| Which customers are about to churn | revenue + product |
| Which channels bring customers who stay | marketing + revenue |
| Where the funnel actually leaks | web + product + revenue |
| Whether content investment pays back | ai-search-visibility + web + revenue |

Every one of these depends on a stable shared identifier existing between the
two sources. When it does not, that is the work, and the skills say so rather
than producing a number from whichever side is available.
