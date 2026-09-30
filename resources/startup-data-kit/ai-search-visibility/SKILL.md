---
name: ai-search-visibility
description: Use when working on SEO, GEO or AEO, measuring whether a brand appears in AI assistant answers, tracking AI crawler traffic from GPTBot or ClaudeBot, analysing Search Console performance, or deciding what content to write for search and AI answer engines.
---

# Search and AI answer visibility

**Status:** experimental · **Risk:** read-only

> **Upstream documentation wins.** Where this file disagrees with the [Bruin
> docs](https://getbruin.com/docs/bruin/overview.html), Google's Search Console
> documentation, or a measurement tool's own documentation, those are right and
> this file is stale. This area moves faster than any other in this repository,
> so treat specifics here as a starting point rather than current fact. Written
> against Bruin CLI `v0.11.765`, checked 2026-09-30.

Three overlapping things sit under this heading:

- **SEO**, ranking in classic search results. Mature, measurable, Search Console.
- **GEO / AEO**, appearing in AI-generated answers. New, measurable only through
  third-party sampling, and heavily hyped.
- **AI crawler traffic**, whether assistants are fetching the site at all.
  Measurable from server logs today.

Be straight about which of the three a question is actually about. They need
different data and have very different evidence quality.

Setup is in the `bruin-agent` skill. This assumes a project exists.

## Look it up live

This file says what to reach for and what to be careful about. For the facts
themselves, ask the tool, and tell the user if it disagrees with this file:

- **Flags:** `bruin <command> --help`. The docs lag the CLI.
- **Docs:** the local Bruin MCP server, `bruin_get_doc_content('<path>')`, or
  `https://getbruin.com/docs/bruin/<path>.html` without it. For this skill:
  `ingestion/gsc` and `ingestion/google_analytics` for the Google connectors,
  `getting-started/templates-docs/google-web-analytics-README` for the template
  that models both exports, `ingestion/s3` and `ingestion/gcs` for loading log
  files, and `ingestion/g2` and `ingestion/trustpilot` for review sites.
- **The user's environment:** Bruin Cloud MCP, or
  `bruin cloud ... --output json`.

**Credentials.** Never ask for one in chat or pass one as a command argument.
For a source, the user runs `bruin connections add` with no flags (the
interactive prompt; its flag mode puts the secret on the command line) or
references `${VAR}` in `.bruin.yml`. For Cloud, `bruin cloud login` or an
exported `BRUIN_CLOUD_API_KEY`, never `--api-key`. `bruin auth status` shows
which is active without printing it.

## What Bruin can ingest directly

- **Search Console performance:** `ingestion/gsc`. The service account has to
  be added as a user on the property before anything loads.
- **GA4, for what search traffic then does:** `ingestion/google_analytics`.
- **Both, already exported to BigQuery:** the `google-web-analytics` template.
- **Server and CDN logs, for crawler traffic:** `ingestion/s3` or
  `ingestion/gcs`. See below.
- **Review-site presence:** `ingestion/g2`, `ingestion/trustpilot`.

**There is no Bruin connector for AI answer visibility.** That measurement comes
from third-party tools that sample assistant responses on a schedule. Say so
rather than implying the pipeline can produce it.

Cloudflare Radar (`ingestion/cloudflare-radar`) is Internet-wide aggregate data,
not this site's traffic or crawler logs. Use it for context only.

## Search Console, the honest baseline

This is where real, verifiable data lives.

- No sessions, no revenue. GSC clicks will not match GA4 organic sessions.
- Roughly 16 months of history. Load it into the warehouse if longer matters.
- Two to three days of lag, and past days are revised in place. Leave the most
  recent days out of any comparison.
- Anonymised queries are excluded from query-level rows but counted in totals,
  so breakdowns will not sum to the total. Do not try to reconcile them.
- Average position is an average across impressions, weighted oddly. Averaging
  it across queries compounds the problem. Prefer distributions.

If the user is on the `google-web-analytics` template, it already builds query
opportunities (`gsc_query_opportunities`), page decay (`gsc_page_trend`), new
and lost queries (`gsc_new_and_lost_queries`) and the landing-page join to GA4
(`ga4_gsc_landing_page_performance`). Read its README and use those before
writing your own. Which organic pages produce paying customers still needs a
landing-page-to-signup key.

## Measuring AI answer visibility

There is no crawl you can run to answer "do we appear in ChatGPT". Assistant
answers vary by user, by session, by phrasing and by date. Any measurement is
sampling, not observation.

What that means in practice:

- **Sampling tools** run a fixed prompt set on a schedule against several
  assistants and record whether a brand was mentioned and which sources were
  cited. [Peec AI](https://peec.ai) is one such tool and exposes an MCP server,
  so an agent can query it directly. There are others. None of them observe real
  user conversations.
- **Brand mention and source citation are independent.** Being cited as a source
  and being recommended are different outcomes and need separate reads.
- **Prompt sets determine the score.** Adding, removing or reweighting prompts
  moves visibility without anything changing about what assistants say. Never
  treat prompt-set changes as an improvement, and be suspicious of branded
  prompts, which score high only because the brand is in the question.
- **Position and share of voice** are only comparable within a fixed prompt set
  over time.

When asked "how visible are we in AI search", the honest answer names the tool,
the prompt set, the assistants sampled, and the date range. Without those the
number means nothing.

## AI crawler traffic, the measurable part

Server and CDN logs show which AI crawlers fetch the site. This is real
observation rather than sampling, and it is underused.

Common agents to look for: `GPTBot`, `OAI-SearchBot`, `ChatGPT-User`,
`ClaudeBot`, `Claude-User`, `PerplexityBot`, `Google-Extended`, `Bytespider`,
`Applebot-Extended`, `CCBot`.

Worth distinguishing: training crawlers, search-index crawlers, and live
user-triggered fetches. A live fetch means a real person asked something and an
assistant went to the site to answer it, which is the closest thing to a
conversion signal this category has.

Ingest logs from wherever the stack writes them, through `ingestion/s3` or
`ingestion/gcs`. Both read CSV, JSONL and Parquet, so a log in any other shape
needs converting before it loads. Check `robots.txt` first: if these agents are
disallowed, absence is the explanation and no amount of content work will
change it.

## Referral traffic from assistants

GA4 shows referrals from `chatgpt.com`, `perplexity.ai`, `claude.ai` and
similar. Volumes are usually small but the traffic often converts unusually well,
because the person arrived with intent already formed.

Track it as its own channel rather than letting it fall into direct or generic
referral. It is the only place where AI visibility connects to revenue with
evidence rather than inference.

## Content work: what the evidence actually supports

Keep recommendations to things with a mechanism, not a listicle.

Reasonable:

- Answer a specific question directly and early on the page. Both search
  features and assistants extract passages.
- Keep facts current and dated. Stale figures get cited and embarrass you.
- Structured data where it maps to a real entity or product.
- Be citable: clear claims, primary sources, a stable URL.
- Presence on the sites assistants actually cite for your category, which is
  often documentation, comparison sites and communities rather than your blog.
- Allow the crawlers you want to be cited by.

Unsupported, and worth pushing back on:

- `llms.txt` as a ranking lever. No major assistant has committed to it.
- Keyword density, word count targets, and generated content at volume.
- Any claim of a fixed technique that "gets you into ChatGPT".

Google's own guidance for AI search still points back to useful, original,
trustworthy content. Say that when asked for a shortcut.

## Never

- **Ask for a credential** in chat or as a command argument. A Google service
  account key is a private key. See **Credentials** above.
- **Publish content.** Drafting is fine; pushing to a CMS, a repository or a
  live site is a write. Propose it and let a person publish.
- **Change `robots.txt` or crawler directives** without explicit approval. A
  wrong line here can deindex a site.
- **Put a raw URL in output without stripping its parameters.** Query strings
  carry session tokens, reset links and personal data.

## What this cannot tell you

| Asked | Actually needed |
|---|---|
| "Are we in ChatGPT?" | A sampled prompt set with a stated date. There is no ground truth. |
| "Why did rankings drop?" | Usually an algorithm update or a site change. Check the deploy log and update timelines before theorising. |
| "How much revenue does SEO bring?" | Landing page carried through to signup and payment. Without that key, organic stops at clicks. |
| "What should we write next?" | A gap between what people ask and what the site answers. GSC impressions without clicks is the best available proxy. |

Report what is measured, what is sampled, and what is inferred. In this category
that distinction matters more than in any other.

## Reference

- Traffic side: [../web-analytics/SKILL.md](../web-analytics/SKILL.md)
