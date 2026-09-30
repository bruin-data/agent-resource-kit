# Startup data kit

> **Upstream documentation wins.** Where a skill here disagrees with the tool's
> own documentation or its `--help` output, upstream is right and the file here
> is stale. Each skill states the version and date it was written against.
> Checked 2026-09-29.

Answering business questions from a startup's data. One resource per domain,
because the traps are domain-specific: what ruins a revenue number is not what
ruins an attribution number.

Each folder is an independent skill. Take the ones you need.

| Resource | Domain | Main sources |
|---|---|---|
| [`revenue-analytics`](revenue-analytics/) | Finance and billing | Stripe, Chargebee, Paddle, RevenueCat, Shopify |
| [`marketing-analytics`](marketing-analytics/) | Advertising, lifecycle, CRM | Google Ads, Meta, TikTok, LinkedIn, HubSpot, Klaviyo, Salesforce |
| [`product-analytics`](product-analytics/) | Usage and activation | PostHog, Mixpanel, Amplitude, Firebase |
| [`web-analytics`](web-analytics/) | Traffic and acquisition | GA4, Search Console |
| [`ai-search-visibility`](ai-search-visibility/) | SEO, GEO, AEO | Search Console, server logs, third-party sampling tools |

## Start here

Set up Bruin first with [`../bruin-agent`](../bruin-agent/): CLI, project,
template, connection, agent skills.

Then take the domain that answers the question you actually have. Most startups
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
