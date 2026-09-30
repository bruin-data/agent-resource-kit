# linkedin-enrichment

A command-line tool that pulls public LinkedIn data through
[Apify](https://apify.com) actors: company profiles, person profiles, people
and company search, post search, one person's post history, job search and job
detail. Results are cached in a local SQLite file so the same lookup is not
paid for twice.

> **Example code, provided as-is. Not part of the Bruin platform** and not a
> supported Bruin product. It is a sample you configure, review and run
> yourself, with your own credentials and your own Apify account. No support
> agreement or SLA covers it. See the repository
> [LICENSE](../../../LICENSE) for the warranty disclaimer.

> **Apify is a paid third-party service.** You need your own Apify account and
> your own token. Every command that is not answered from the local cache
> starts an actor run, and actor runs cost money on your account. Pricing, rate
> limits and terms are between you and Apify, and between you and each actor's
> author. Nothing here is an endorsement, and none of these actors are
> maintained by this repository.

> **Scraping LinkedIn may conflict with LinkedIn's User Agreement.** LinkedIn
> restricts automated collection, and enforcement is theirs to apply. Whether
> your use is lawful and permissible is yours to assess, with your own legal
> advice. Running this tool is a decision you are making, not one this
> repository has made for you.

> **Upstream documentation wins.** Where anything here disagrees with
> [Apify's documentation](https://docs.apify.com/) or an actor's own page on
> the Apify Store, upstream is right and this file is stale. Written against
> the Apify REST API v2 as documented and checked 2026-09-29. The actor input
> and output shapes came from a private tool that ran them earlier in 2026 and
> have not been re-verified against a live account since. Actors change without
> notice.

## Personal data, and your obligations

This tool collects personal data about identifiable people: names, employers,
job histories, locations, what they have posted. That it is publicly visible on
a website does not make it unregulated.

- **You are the controller** of everything you collect with it. Under the GDPR,
  the UK GDPR and similar regimes you need a lawful basis, and "it was public"
  is not one on its own. Legitimate interest has to be assessed and recorded,
  and transparency and erasure duties still apply to data you scraped rather
  than were given.
- **The cache is a data store.** `linkedin-cache.db` holds raw profiles on your
  disk. Gitignore it, keep it out of backups you do not control, and delete
  what you no longer need: `cache-clear --older-than-days 30 --yes`, or
  `cache-clear --yes` for all of it.
- **Do not paste whole profiles into an agent transcript.** A transcript goes
  to a model provider, is usually retained, and cannot be recalled. Pass the
  fields you actually need for the task at hand, not the record.
- **Do not use it for automated decisions about people** (hiring screens,
  credit, ranking candidates) without checking what that requires of you.
- Keep to what you need for a stated purpose, and delete it when that purpose
  is done.

If you cannot say what your lawful basis is, that is the answer: do not run it.

## Install

Python 3.9 or newer.

```bash
cd linkedin-enrichment
pip install -r requirements.txt
python3 scripts/cli.py --help
```

`requests` is the only hard dependency. `PyYAML` is needed only if you use a
YAML config file. The cache uses `sqlite3` from the standard library.

## Get an API token

In the Apify console: **Settings → Integrations → API tokens → create a new
token**. Copy it once.

The token is account-wide: it can start any actor and spend your credits. Set a
spending limit on the account before you start, and treat the token as you
would a payment credential.

## Set the environment variable

The token is read from `APIFY_API_TOKEN` and from nowhere else. There is no
flag and no config key for it, deliberately: a flag would land in your shell
history and in the process list.

```bash
export APIFY_API_TOKEN='...'          # current shell only
```

For something persistent, use a file your shell loads and git ignores:

- [direnv](https://direnv.net): put `export APIFY_API_TOKEN=...` in `.envrc`,
  then `direnv allow`.
- A `.env` loaded by your shell or `dotenv`.
- Your password manager's CLI, e.g. `export APIFY_API_TOKEN=$(op read ...)`.

Add `.env` and `.envrc` to `.gitignore` **before** you write the token into
them. If a token is committed or pasted into a chat, revoke it in the Apify
console and issue a new one; there is no other way to un-share it.

## Configure

Optional. Copy `config.example.yml` to `linkedin-enrichment.yml` to change the
cache path, the default cache age, or which Apify actor backs a command. Actor
ids are the thing here most likely to go stale: an actor can be retired or
replaced by a cheaper one at any time.

No credential belongs in this file.

## Commands

Everything the cache can answer runs freely. Everything else prints what it
would fetch and stops, until you add `--yes`.

```bash
# detail: one record per identifier
python3 scripts/cli.py company google 1441 --yes
python3 scripts/cli.py profile williamhgates --yes
python3 scripts/cli.py job 4011051212 --yes

# discovery: one query, a page of results
python3 scripts/cli.py people-search --lastname Hopper --title "Rear Admiral" --yes
python3 scripts/cli.py company-search "mobile gaming analytics" --page 1 --yes
python3 scripts/cli.py post-search --keyword "data engineering" \
    --date-filter past-week --yes
python3 scripts/cli.py profile-posts williamhgates --total-posts 50 --yes
python3 scripts/cli.py job-search --keywords engineer --location London --yes

# the local cache
python3 scripts/cli.py cache-info
python3 scripts/cli.py cache-clear --kind profile --yes
```

Useful flags on every fetching command: `--max-age-days N` (how old a cached
row may be), `--no-cache` (ignore the cache completely, neither read nor
write), `--cache-path PATH`, `--output-dir DIR` (also write the raw actor
output, one JSON file per result), `--run-timeout SECONDS`.

The manifest goes to stdout as JSON and nothing else does; progress, the
confirmation gate and warnings go to stderr. So `... --yes > out.json` gives
you a clean file.

Exit codes: `0` success, `1` error, `2` a run that was not confirmed.

Discovery first, then detail: `people-search` and `company-search` return a
short list with a `slug` and a `linkedin_id` per hit; feed the right one into
`profile` or `company`. Prefer the numeric `linkedin_id` for companies, since a
vanity slug changes when LinkedIn renames it.

## Costs and rate limits

- **Every miss is a paid actor run.** A dry run (no `--yes`) tells you how many
  records would be fetched before you commit to it.
- **Cached reads are free** and need no token at all. The default cache life is
  30 days, or 3 days for post history, whose engagement counts move hourly.
- **Actors are priced by their authors**, usually per result or per compute
  unit, on top of your Apify plan. Check the actor's page on the Apify Store
  for its current price; this file deliberately quotes no numbers, because they
  change.
- **There is no retry and no backoff.** An HTTP 429 from Apify surfaces as an
  error; wait and re-run. The cache means a re-run costs nothing for whatever
  already came back.
- **A run you interrupt keeps running.** Ctrl-C, or a `--run-timeout` that
  expires, stops this tool waiting; it does not stop the actor or the billing.
  Abort it in the Apify console.
- Set a spending limit on your Apify account. It is the control that actually
  holds; the `--yes` gate is a seatbelt, not a budget.

## Limitations

- **Coverage is uneven.** Privacy-locked and low-profile accounts are missing
  or thin. An empty people search comes back as a placeholder row rather than
  zero results; the CLI drops it, so no results means no results.
- **Actor output shapes drift.** Field names vary between actor versions, so
  every extractor probes a set of aliases and a field it cannot find becomes
  `null`. The summary in the manifest is a convenience; `--output-dir` gives
  you what the actor actually returned, which is what to parse.
- **Identifiers do not all interoperate.** `linkedin_id` means a numeric
  company id for companies, an `ACoA…` member URN for people from
  `profile` and `people-search`, and the author's username for
  `profile-posts`. Do not join across them without checking.
- **The cache is local and per file.** No sharing across a team, no
  concurrency story beyond SQLite's own locking, and it is append-only until
  you clear it.
- **Pagination is manual.** One command invocation is one page, unless the
  actor supports `--total-posts` and you use it.
- **Nothing is normalised.** If an actor returns followers as `"70K
  followers"`, that string is what you get.
- **Sales Navigator search and email guessing were deliberately left out**;
  see the note at the end of `SKILL.md`.
- Endpoint and actor behaviour came from documentation and from earlier runs,
  not from a live run of every command in this repository. Check the responses
  you get.
