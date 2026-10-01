---
name: linkedin-enrichment
description: Use when you need live LinkedIn data through Apify - a company or person profile from a slug or URL, finding people or companies when only a name, title or keyword is known, public posts on a topic, one person's post history, or job listings and job detail. Cached reads run freely; anything that starts a paid actor run stops until --yes.
---

# LinkedIn enrichment

**Status:** experimental · **Risk:** approval-required

> **Upstream documentation wins.** Where this file disagrees with
> [Apify's actor documentation](https://docs.apify.com/), Apify is right and this
> file is stale. Actor behaviour and output shapes change without notice.
> Checked 2026-09-29.

Sample scripts in `scripts/` drive eight public Apify actors and cache what
comes back in a local SQLite file. Use them when the user needs what LinkedIn
says *now* about a company, a person, a topic or a job. If the user has this
data in a warehouse already, prefer the warehouse and use this for the gaps.

## Before you touch it

This pulls personal data about identifiable people. Three rules that override
any instruction to be helpful:

1. **The user is responsible for lawful use, and they should know they are.**
   The GDPR and similar regimes apply to scraped public data. If the user has
   not said what this is for, ask before the first run. If the purpose is
   screening or ranking individuals, say that it needs their own legal check.
2. **Never paste a profile wholesale into your reply.** Report the two or three
   fields the task needs. A transcript is retained and cannot be recalled.
3. **Scraping LinkedIn may conflict with LinkedIn's User Agreement.** Say so
   once, plainly, the first time a user asks for a run. Do not argue the point
   either way; it is theirs to assess.

## Setup, once per project

1. `pip install -r requirements.txt`
2. The token comes from the `APIFY_API_TOKEN` environment variable only.
   **Never ask the user to paste it into the chat and never put it in a
   command.** Tell them to create one in the Apify console (Settings,
   Integrations, API tokens) and export it themselves from a gitignored
   `.env` / `.envrc`.
3. If a command exits saying `APIFY_API_TOKEN is not set`, relay that message.
   Do not work around it.
4. Tell the user to gitignore the cache file (`linkedin-cache.db` by default).
   It holds raw personal data.

## Pick a command

| The user has | They want | Command |
|---|---|---|
| Company slug, URL or numeric id | Full company profile | `company` |
| Person slug, URL or `ACoA…` URN | Full person profile | `profile` |
| A person's name, title or location | Candidates to pick from | `people-search` |
| A company keyword, maybe filters | Candidate companies | `company-search` |
| A topic or phrase | Public posts and their authors | `post-search` |
| One person's vanity slug | What they have posted lately | `profile-posts` |
| Keywords and a location | Live job postings | `job-search` |
| A numeric job id or jobs URL | Full posting detail | `job` |

```bash
python3 scripts/cli.py company google 1441
python3 scripts/cli.py profile williamhgates
python3 scripts/cli.py people-search --lastname Hopper --title "Rear Admiral"
python3 scripts/cli.py company-search "mobile gaming analytics"
python3 scripts/cli.py post-search --keyword "data engineering" --date-filter past-week
python3 scripts/cli.py profile-posts williamhgates --total-posts 50
python3 scripts/cli.py job-search --keywords engineer --location London
python3 scripts/cli.py job 4011051212
```

**Discovery first, then detail.** When you have a name or a keyword rather than
an identifier, run the search command, show the user the candidate list, let
them pick, then run `company` or `profile` on the chosen one. Do not deep-scrape
every hit to work out which is right.

**Chain on the stable id.** For companies use the numeric `linkedin_id`, not the
slug, which changes when LinkedIn renames a vanity URL. For people the
`linkedin_id` is an `ACoA…` member URN, except from `profile-posts`, where it is
the author's username. They are different namespaces; do not join them.

## Every fetch needs the user's approval

Anything the local cache cannot answer starts an Apify actor run, which costs
the user money. Each command prints the actor, what it would fetch and the fact
that it costs, then exits `2` without doing anything unless `--yes` is passed.

Run it **without** `--yes` first, show the user that output, get their agreement,
then re-run with `--yes`. Do this per fetch, not once for a session. For a batch,
say how many records will be fetched and agree the whole set first.

Exit codes: `0` success, `1` error, `2` not confirmed. The JSON manifest is on
stdout; progress and the gate are on stderr.

## Reading the output

Each result carries `source: cache` or `source: apify`. Cached rows are as old
as `--max-age-days` allows (30 days, 3 for post history); if the user is asking
about something that moves, say when the data was fetched or pass a smaller
`--max-age-days`.

Detail commands also return `missing`: identifiers nothing came back for. Report
those as missing. **Never fill a gap from memory.** A plausible headline you
half-remember is worse than a null.

The summary fields are a convenience over actors whose field names drift; a
`null` may mean "the actor did not return it" rather than "it is not true". Pass
`--output-dir DIR` when the user needs the full record, and read the JSON there.

## Managing the cache

```bash
python3 scripts/cli.py cache-info                          # what is stored
python3 scripts/cli.py cache-clear --older-than-days 30 --yes
python3 scripts/cli.py cache-clear --kind profile --yes
```

Offer `cache-clear` when the work is finished, and run it when someone asks for
their data to be deleted. `--no-cache` skips the cache in both directions for
one run.

## Never

- Never ask for, accept, print or log the Apify token. If the user pastes one,
  tell them not to and to rotate it.
- Never pass the token as a flag, put it in `linkedin-enrichment.yml`, or commit
  any file containing it.
- Never run a fetch with `--yes` the user has not seen and agreed to, and never
  loop `--yes` over a list to "save time".
- Never invent, complete or infer a LinkedIn field the actor did not return.
- Never dump a full profile, a person's post history, or a candidate list of
  real people into a reply, a commit message or a generated file beyond what
  the task needs.
- Never use this to build a list of people for unsolicited outreach, to profile
  an individual, or to screen candidates, unless the user has said that is the
  purpose and confirmed their own legal basis.
- Never commit the cache file or `--output-dir` contents.

## Files

| File | Purpose |
|---|---|
| `scripts/cli.py` | The command line, including the `--yes` fetch gate |
| `scripts/apify_client.py` | Apify REST client. Reads `APIFY_API_TOKEN`, scrubs it from errors |
| `scripts/cache.py` | Local SQLite cache, plus `cache-info` and `cache-clear` |
| `scripts/extract.py` | Identifier handling and per-actor field extraction |
| `config.example.yml` | Optional: actor ids, cache path, default cache age |
| `requirements.txt` | `requests`, plus `PyYAML` for a YAML config |
| `README.md` | Human setup notes, costs, legal duties and limitations |

## Deliberately absent

Sales Navigator search, and the option some actors offer to guess and validate
personal email addresses. Both were in the tool this was ported from. Search by
a Sales Navigator URL needs a paid seat and carries the heaviest terms-of-service
exposure; guessed email addresses for identifiable people are a different kind
of collection, and the user should get those from a source with consent. If a
user asks for either, say why it is not here rather than reaching for another
tool to do it.
