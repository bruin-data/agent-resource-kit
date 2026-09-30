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
> against Bruin CLI `v0.11.765`, checked 2026-09-29.

Three overlapping things sit under this heading:

- **SEO**, ranking in classic search results. Mature, measurable, Search Console.
- **GEO / AEO**, appearing in AI-generated answers. New, measurable only through
  third-party sampling, and heavily hyped.
- **AI crawler traffic**, whether assistants are fetching the site at all.
  Measurable from server logs today.

Be straight about which of the three a question is actually about. They need
different data and have very different evidence quality.

Setup is in the `bruin-agent` skill. This assumes a project exists.

## What Bruin can ingest directly

| Need | Connector |
|---|---|
| Search Console performance | `gsc` (service account JSON plus site URL) |
| GA4, for what search traffic then does | `googleanalytics` |
| Both, already exported to BigQuery | `bruin init google-web-analytics` |
| Edge and bot traffic patterns | `cloudflare_radar` |
| Review-site presence | `g2`, `trustpilot` |

**There is no Bruin connector for AI answer visibility.** That measurement comes
from third-party tools that sample assistant responses on a schedule. Say so
rather than implying the pipeline can produce it.

## Search Console, the honest baseline

This is where real, verifiable data lives.

- Clicks, impressions, CTR and average position. No sessions, no revenue.
- 16 months of history maximum. Load it into the warehouse if longer matters.
- Anonymised queries are excluded from query-level rows but counted in totals,
  so breakdowns will not sum to the total. Do not try to reconcile them.
- Average position is an average across impressions, weighted oddly. Averaging
  it across queries compounds the problem. Prefer distributions.
- GSC clicks will not match GA4 organic sessions. Different measurement points.

Useful joins once it is in the warehouse: query and page performance over time,
pages gaining or losing impressions, queries where position improved but clicks
did not, and, if a landing-page-to-signup key exists, which organic pages
produce paying customers.

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

Ingest logs from `s3`, `gcs` or `cloudflare_radar` depending on the stack. Check
`robots.txt` first: if these agents are disallowed, absence is the explanation
and no amount of content work will change it.

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

- **Ask for a credential** in chat. GSC uses service account JSON, a private key.
  Route through `bruin connections add` or an environment variable.
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

- Google web analytics template: https://getbruin.com/docs/bruin/getting-started/templates.html
- Ingestr sources: https://getbruin.com/docs/ingestr/
- Traffic side: [../web-analytics/SKILL.md](../web-analytics/SKILL.md)
