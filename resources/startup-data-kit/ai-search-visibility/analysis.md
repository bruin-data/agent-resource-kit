# Answering search and AI visibility questions

> **Upstream documentation wins.** Where this file disagrees with the [Bruin
> docs](https://getbruin.com/docs/bruin/overview.html), Google's Search Console
> documentation, or a measurement tool's own documentation, those are right and
> this file is stale. This area moves faster than any other in this repository,
> so treat specifics here as a starting point rather than current fact. Written
> against Bruin CLI `v0.11.765`, checked 2026-10-01.

Read this once data exists and the user is asking questions of it. If
`decisions.md` sits beside the pipeline's `pipeline.yml`, read it first: it
records which choices this setup follows. The `Never` rules in `SKILL.md` apply
here too.

## Before answering

1. **Name which of the three the question is about.** SEO, AI answer
   visibility, or AI crawler traffic. They need different data and have very
   different evidence quality.
2. **Read the model before querying it.** If the user is on a template, read its
   report assets and their descriptions before writing any SQL.
3. **Check freshness first.** Read the last runs from Bruin Cloud MCP or
   `bruin cloud runs list --output json`, then the maximum date in the raw
   table.

## Search Console, the honest baseline

This is where real, verifiable data lives.

- No sessions, no revenue. GSC clicks will not match GA4 organic sessions.
- Roughly 16 months of history through the API. Load it into the warehouse if
  longer matters. The bulk data export starts the day it was enabled and does
  not backfill.
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
writing your own. Its value columns are modelled from weights on key events, not
recognised revenue, so say so. Which organic pages produce paying customers
still needs a landing-page-to-signup key.

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

Check `robots.txt` first: if these agents are disallowed, absence is the
explanation and no amount of content work will change it.

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
