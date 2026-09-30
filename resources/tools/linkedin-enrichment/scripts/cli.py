#!/usr/bin/env python3
"""Command-line front end for LinkedIn enrichment via Apify actors.

Example code, provided as-is. Not part of the Bruin platform.

    python3 cli.py company google --yes
    python3 cli.py people-search --lastname Hopper --title "Rear Admiral"
    python3 cli.py cache-info

Anything served from the local cache runs freely. Anything that would start an
Apify actor run prints what it is about to fetch and then stops unless ``--yes``
is given, because a run costs money on your Apify account and pulls other
people's personal data. The same command without ``--yes`` is a safe dry run.

The API token comes from the APIFY_API_TOKEN environment variable only; see
apify_client.py.

Output: the manifest goes to stdout as JSON and nothing else does. Progress,
the confirmation gate and every warning go to stderr, so stdout stays
parseable.

Legal and ethical note, repeated in the README and SKILL.md because it matters
more than any flag here: this pulls personal data about identifiable people
from a site whose terms restrict automated collection. You are the controller
of what you collect. Have a lawful basis, keep only what you need, honour
erasure requests (``cache-clear``), and do not paste whole profiles into an
agent transcript.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

try:  # Run as a module (python3 -m scripts.cli) or as a plain script.
    from .apify_client import ApifyClient, ApifyError, MissingCredential
    from .cache import Cache, canonical_query, default_cache_path
    from . import extract
except ImportError:  # pragma: no cover - depends on invocation style
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from apify_client import ApifyClient, ApifyError, MissingCredential
    from cache import Cache, canonical_query, default_cache_path
    import extract

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_NOT_CONFIRMED = 2

CONFIG_ENV = "LINKEDIN_ENRICHMENT_CONFIG"
CONFIG_FILENAMES = (
    "linkedin-enrichment.yml",
    "linkedin-enrichment.yaml",
    "linkedin-enrichment.json",
)

DEFAULT_MAX_AGE_DAYS = 30
# Post engagement counts move hourly, so post history defaults to a short life.
DEFAULT_POST_MAX_AGE_DAYS = 3

# These actors reject input arrays longer than this, and reject duplicates.
ACTOR_INPUT_CHUNK = 1000

# Public Apify Store actors. They are third-party software: a maintainer can
# change the output shape, change the price or take the actor down, and none of
# that is announced here. Override any of them in the config file.
DEFAULT_ACTORS = {
    "company": "ipHw77V2NMJPy8sbS",
    "profile": "yZnhB5JewWf9xSmoM",
    "people-search": "pIyH7237rHZBxoO7q",
    "company-search": "QwLfX9hYQXhA84LY3",
    "post-search": "5QnEH5N71IK2mFLrP",
    "profile-posts": "LQQIXN9Othf8f7R5n",
    "job-search": "KE649tixwpoRnZtJJ",
    "job": "39xxtfNEwIEQ1hRiM",
}


# ---------------------------------------------------------------------------
# Configuration
#
# The config file is optional and holds no credential. It exists because actor
# ids are the one thing here that genuinely goes stale: an actor can be
# deprecated or replaced by a cheaper one without this file changing.
# ---------------------------------------------------------------------------


class Config:
    def __init__(
        self, raw: Optional[Dict[str, Any]] = None, path: Optional[str] = None
    ) -> None:
        raw = raw or {}
        self.path = path
        self.defaults: Dict[str, Any] = raw.get("defaults") or {}
        self._actors: Dict[str, Any] = raw.get("actors") or {}

    def actor(self, command: str) -> str:
        value = self._actors.get(command)
        if isinstance(value, str) and value.strip():
            return value.strip()
        return DEFAULT_ACTORS[command]

    @property
    def cache_path(self) -> Optional[str]:
        value = self.defaults.get("cache_path")
        return value if isinstance(value, str) and value.strip() else None

    def max_age_days(self, fallback: float) -> float:
        value = self.defaults.get("max_age_days")
        try:
            return float(value) if value is not None else fallback
        except (TypeError, ValueError):
            return fallback


def load_config(explicit_path: Optional[str]) -> Config:
    """Load config from --config, then $LINKEDIN_ENRICHMENT_CONFIG, then cwd."""
    path = explicit_path or os.environ.get(CONFIG_ENV)
    if not path:
        for name in CONFIG_FILENAMES:
            candidate = os.path.join(os.getcwd(), name)
            if os.path.isfile(candidate):
                path = candidate
                break
    if not path:
        return Config()
    if not os.path.isfile(path):
        raise SystemExit(f"config file not found: {path}")

    with open(path, "r", encoding="utf-8") as handle:
        if path.endswith(".json"):
            raw = json.load(handle)
        else:
            try:
                import yaml  # lazy, so PyYAML is only needed for a YAML config
            except ImportError:
                raise SystemExit(
                    "PyYAML is required to read a YAML config file: "
                    "pip install PyYAML (or use a .json config)"
                )
            raw = yaml.safe_load(handle) or {}
    if not isinstance(raw, dict):
        raise SystemExit(f"config file {path} must contain a mapping at the top")
    unknown = set(raw) - {"defaults", "actors"}
    if unknown:
        warn(f"ignoring unknown config key(s): {', '.join(sorted(unknown))}")
    return Config(raw, path)


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


def warn(message: str) -> None:
    print(message, file=sys.stderr)


def emit(manifest: Dict[str, Any]) -> None:
    """The one thing that writes to stdout."""
    print(json.dumps(manifest, indent=2, default=str, ensure_ascii=False))


def write_file(directory: str, name: str, payload: Any) -> str:
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, name)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, default=str, ensure_ascii=False)
    return path


def unique_name(stem: str, used: set) -> str:
    """A name unique within this run. A re-run overwrites its own files."""
    name = f"{stem}.json"
    suffix = 1
    while name in used:
        name = f"{stem}-{suffix}.json"
        suffix += 1
    used.add(name)
    return name


# ---------------------------------------------------------------------------
# The gate
# ---------------------------------------------------------------------------


def confirm_run(args: argparse.Namespace, actor_id: str, what: str) -> bool:
    """Show the run that is about to be paid for, then require --yes.

    Returns False when the caller should stop. Reads served from the cache do
    not come through here; only a call that would start an actor does.
    """
    warn("About to start an Apify actor run:")
    warn(f"  actor:   {actor_id}")
    warn(f"  fetch:   {what}")
    warn("  cost:    consumes credits on your Apify account")
    warn("  data:    pulls personal data about identifiable people")
    if getattr(args, "yes", False):
        return True
    warn("")
    warn(
        "Nothing was fetched. Re-run the same command with --yes to start "
        "the run."
    )
    return False


# ---------------------------------------------------------------------------
# Shared plumbing
# ---------------------------------------------------------------------------


def open_cache(args: argparse.Namespace, cfg: Config) -> Cache:
    if getattr(args, "no_cache", False):
        return Cache(None)
    path = (
        getattr(args, "cache_path", None)
        or os.environ.get("LINKEDIN_CACHE_PATH")
        or cfg.cache_path
        or default_cache_path()
    )
    return Cache(path)


def make_client(args: argparse.Namespace) -> ApifyClient:
    return ApifyClient(timeout=getattr(args, "http_timeout", 60))


def dedupe(values: Sequence[Any]) -> List[Any]:
    seen = set()
    out = []
    for value in values:
        key = value if isinstance(value, str) else json.dumps(value, sort_keys=True)
        if key in seen:
            continue
        seen.add(key)
        out.append(value)
    return out


def chunked_actor_call(
    client: ApifyClient,
    args: argparse.Namespace,
    actor_id: str,
    input_key: str,
    values: List[Any],
    base_input: Optional[Dict[str, Any]] = None,
) -> Tuple[List[Dict[str, Any]], Optional[str], Optional[str]]:
    """Call an actor in chunks, deduping the input array first.

    Returns (items, first run id, first dataset id). Provenance is stamped from
    the first chunk, which is enough to find the run again in the console.
    """
    unique = dedupe(values)
    dropped = len(values) - len(unique)
    if dropped:
        warn(f"  deduped {dropped} duplicate input(s) before the run")

    items: List[Dict[str, Any]] = []
    run_id: Optional[str] = None
    dataset_id: Optional[str] = None
    chunks = [
        unique[i : i + ACTOR_INPUT_CHUNK]
        for i in range(0, len(unique), ACTOR_INPUT_CHUNK)
    ]
    for number, chunk in enumerate(chunks, 1):
        if len(chunks) > 1:
            warn(f"  chunk {number}/{len(chunks)} ({len(chunk)} item(s))")
        run_input = dict(base_input or {})
        run_input[input_key] = chunk
        run = client.run_actor(
            actor_id, run_input, timeout_s=args.run_timeout
        )
        if run_id is None:
            run_id = run.get("id")
            dataset_id = run.get("defaultDatasetId")
        warn(f"  run {run.get('id')} dataset {run.get('defaultDatasetId')}")
        items.extend(client.dataset_items(run["defaultDatasetId"]))
    return items, run_id, dataset_id


# ---------------------------------------------------------------------------
# Detail commands: company, profile, job
# ---------------------------------------------------------------------------


def run_detail(
    args: argparse.Namespace,
    cfg: Config,
    kind: str,
    actor_id: str,
    ledger: List[Dict[str, Any]],
    input_key: str,
    to_value: Callable[[Dict[str, Any]], Any],
    attribute: Callable[[Dict[str, Any], str], Tuple[Optional[str], str]],
    summary: Callable[[Dict[str, Any]], Dict[str, Any]],
    base_input: Optional[Dict[str, Any]] = None,
    input_echo: Optional[Callable[[Dict[str, Any]], Optional[str]]] = None,
    index_fallback: bool = False,
) -> int:
    """Cache, then gate, then actor, then cache again.

    ``ledger`` is one record per identifier the user typed, already classified.
    """
    results: List[Dict[str, Any]] = []
    used_names: set = set()

    with open_cache(args, cfg) as cache:
        keys = sorted({(rec["key_type"], rec["key"]) for rec in ledger})
        cached = cache.lookup_detail(kind, keys, args.max_age_days)

        def record(rec: Dict[str, Any], item: Dict[str, Any], source: str) -> None:
            fallback = rec.get("slug_hint") or extract.slugify(rec["raw"])
            linkedin_id, slug = attribute(item, fallback)
            row: Dict[str, Any] = {
                "input": rec["raw"],
                "linkedin_id": linkedin_id,
                "slug": slug,
                "source": source,
            }
            row.update(summary(item))
            if args.output_dir:
                name = unique_name(slug or rec["key"], used_names)
                row["path"] = write_file(args.output_dir, name, item)
            results.append(row)
            warn(f"  {source:<6} {slug or linkedin_id or rec['raw']}")

        for rec in ledger:
            item = cached.get((rec["key_type"], rec["key"]))
            if item is None:
                continue
            rec["source"] = "cache"
            record(rec, item, "cache")

        misses = [rec for rec in ledger if not rec.get("source")]

        if misses:
            what = f"{len(misses)} {kind} record(s): " + ", ".join(
                rec["raw"] for rec in misses[:10]
            )
            if len(misses) > 10:
                what += f", and {len(misses) - 10} more"
            if not confirm_run(args, actor_id, what):
                emit(
                    {
                        "kind": kind,
                        "results": results,
                        "not_fetched": [rec["raw"] for rec in misses],
                        "stopped_for_confirmation": True,
                    }
                )
                return EXIT_NOT_CONFIRMED

            client = make_client(args)
            items, run_id, dataset_id = chunked_actor_call(
                client,
                args,
                actor_id,
                input_key,
                [to_value(rec) for rec in misses],
                base_input=base_input,
            )

            by_raw = {rec["raw"]: rec for rec in misses}
            by_key = {
                (rec["key_type"], rec["key"]): rec for rec in misses
            }
            unmatched = list(misses)
            rows_to_cache: List[Dict[str, Any]] = []

            for index, item in enumerate(items):
                response_id, response_slug = attribute(item, "unknown")
                echo = input_echo(item) if input_echo else None
                candidates = [
                    by_raw.get(echo) if echo else None,
                    by_key.get(("id", response_id)) if response_id else None,
                    by_key.get(("slug", response_slug)) if response_slug else None,
                ]
                if index_fallback and index < len(misses):
                    candidates.append(misses[index])

                rec = None
                for candidate in candidates:
                    if candidate is not None and candidate in unmatched:
                        rec = candidate
                        break
                if rec is None:
                    # Nothing reliable to attribute this to. Keep it, but under
                    # the response's own identity, so it cannot overwrite a
                    # record that was matched properly.
                    warn(
                        f"  note   response {index} could not be matched to an "
                        f"input; keeping it under its own identity"
                    )
                    rec = {
                        "raw": echo or response_slug or f"item-{index}",
                        "key_type": "slug",
                        "key": response_slug or f"item-{index}",
                        "slug_hint": response_slug,
                    }
                else:
                    unmatched.remove(rec)
                    rec["source"] = "apify"

                record(rec, item, "apify")
                fallback = rec.get("slug_hint") or extract.slugify(rec["raw"])
                response_id, response_slug = attribute(item, fallback)
                base_row = {
                    "key_type": rec["key_type"],
                    "key": rec["key"],
                    "input": rec["raw"],
                    "actor_id": actor_id,
                    "run_id": run_id,
                    "dataset_id": dataset_id,
                    "data": item,
                }
                rows_to_cache.append(base_row)
                # Cache under the canonical identifiers too, so a later lookup
                # by slug finds a record that was fetched by id, and the other
                # way round.
                for key_type, key in (("id", response_id), ("slug", response_slug)):
                    if key and (key_type, key) != (rec["key_type"], rec["key"]):
                        alias = dict(base_row)
                        alias["key_type"] = key_type
                        alias["key"] = key
                        rows_to_cache.append(alias)

            cache.insert_detail(kind, rows_to_cache)

    missing = sorted(rec["raw"] for rec in ledger if not rec.get("source"))
    if missing:
        warn(f"No data came back for: {', '.join(missing)}")
    emit(
        {
            "kind": kind,
            "results": results,
            "missing": missing,
            "stopped_for_confirmation": False,
        }
    )
    return EXIT_OK


# ---------------------------------------------------------------------------
# Search commands
# ---------------------------------------------------------------------------


def run_search(
    args: argparse.Namespace,
    cfg: Config,
    kind: str,
    actor_id: str,
    query: Dict[str, Any],
    run_input: Dict[str, Any],
    extract_keys: Callable[[Dict[str, Any]], Tuple[Optional[str], Optional[str]]],
    summary: Callable[[Dict[str, Any]], Dict[str, Any]],
    label: str,
    item_transform: Optional[Callable[[List[Any]], List[Dict[str, Any]]]] = None,
    drop_item: Optional[Callable[[Dict[str, Any]], bool]] = None,
) -> int:
    """Cache, then gate, then actor, then cache again, for one query page."""
    with open_cache(args, cfg) as cache:
        cached = cache.lookup_search(kind, query, args.max_age_days)

        if cached is not None:
            items = [row["data"] for row in cached]
            run_id = cached[0]["run_id"]
            source = "cache"
            warn(f"  cache  {len(items)} result(s) from run {run_id}")
        else:
            if not confirm_run(args, actor_id, f"{kind}, {label}"):
                emit(
                    {
                        "kind": kind,
                        "query": query,
                        "results": [],
                        "stopped_for_confirmation": True,
                    }
                )
                return EXIT_NOT_CONFIRMED

            client = make_client(args)
            run = client.run_actor(
                actor_id, run_input, timeout_s=args.run_timeout
            )
            run_id = run.get("id")
            dataset_id = run.get("defaultDatasetId")
            warn(f"  run {run_id} dataset {dataset_id}")
            raw_items = client.dataset_items(dataset_id)
            items = item_transform(raw_items) if item_transform else raw_items
            if drop_item:
                kept = [item for item in items if not drop_item(item)]
                if len(kept) != len(items):
                    warn(
                        f"  dropped {len(items) - len(kept)} empty "
                        f"placeholder row(s); treat them as no result"
                    )
                items = kept
            source = "apify"
            cache.insert_search(
                kind, query, actor_id, run_id, dataset_id, items, extract_keys
            )
            warn(f"  apify  {len(items)} result(s)")

        results = []
        for index, item in enumerate(items):
            row = dict(summary(item))
            if source == "cache":
                row["slug"] = cached[index]["slug"]
                row["linkedin_id"] = cached[index]["linkedin_id"]
            else:
                slug, linkedin_id = extract_keys(item)
                row["slug"] = slug
                row["linkedin_id"] = linkedin_id
            row["source"] = source
            results.append(row)

    manifest: Dict[str, Any] = {
        "kind": kind,
        "query": query,
        "run_id": run_id,
        "results": results,
        "stopped_for_confirmation": False,
    }
    if args.output_dir:
        digest = hashlib.sha256(
            canonical_query(query).encode("utf-8")
        ).hexdigest()[:10]
        stem = f"{kind}-{extract.slugify(label)[:40]}-{digest}"
        manifest["path"] = write_file(
            args.output_dir, f"{stem}.json", {"query": query, "items": items}
        )
    warn(f"Done: {len(results)} result(s) ({source}) for {label}")
    emit(manifest)
    return EXIT_OK


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def bad(message: str) -> int:
    warn(f"error: {message}")
    return EXIT_ERROR


def out_of_range(args: argparse.Namespace, limit_max: int) -> Optional[str]:
    """The shared page and limit checks, so an actor is not paid to reject us."""
    if getattr(args, "page", 1) < 1:
        return "--page must be 1 or more"
    limit = getattr(args, "limit", 1)
    if limit < 1 or limit > limit_max:
        return f"--limit must be between 1 and {limit_max}"
    return None


def cmd_company(cfg: Config, args: argparse.Namespace) -> int:
    ledger = [extract.classify_input(raw, "company") for raw in args.identifiers]
    return run_detail(
        args,
        cfg,
        kind="company",
        actor_id=cfg.actor("company"),
        ledger=ledger,
        input_key="identifier",
        to_value=lambda rec: rec["raw"],
        attribute=extract.company_attribute,
        summary=extract.company_summary,
        input_echo=extract.company_input_echo,
    )


def cmd_profile(cfg: Config, args: argparse.Namespace) -> int:
    ledger = [extract.classify_input(raw, "profile") for raw in args.profiles]
    return run_detail(
        args,
        cfg,
        kind="profile",
        actor_id=cfg.actor("profile"),
        ledger=ledger,
        input_key="urls",
        to_value=lambda rec: {"url": extract.normalise_profile_url(rec["raw"])},
        attribute=extract.profile_attribute,
        summary=extract.profile_summary,
        base_input={"scrapeCompany": bool(args.scrape_company)},
        # This actor does not echo the input back, so attribution relies on the
        # identifiers in the response.
        input_echo=None,
    )


def cmd_job(cfg: Config, args: argparse.Namespace) -> int:
    ledger = []
    unusable = []
    for raw in args.job_ids:
        job_id = extract.extract_job_id(raw)
        if job_id is None:
            unusable.append(raw)
            continue
        ledger.append(
            {"raw": raw, "key_type": "id", "key": job_id, "slug_hint": job_id}
        )
    if unusable:
        warn(f"  no job id found in: {', '.join(unusable)}")
    if not ledger:
        return bad("no usable LinkedIn job ids were given")

    return run_detail(
        args,
        cfg,
        kind="job",
        actor_id=cfg.actor("job"),
        ledger=ledger,
        input_key="job_id",
        to_value=lambda rec: rec["key"],
        attribute=lambda item, fallback: (
            extract.job_id_from_item(item),
            extract.job_id_from_item(item) or fallback,
        ),
        summary=extract.job_summary,
        # Postings carry their own id, but older responses omit it; input order
        # is the documented fallback for this actor.
        index_fallback=True,
    )


def cmd_people_search(cfg: Config, args: argparse.Namespace) -> int:
    fields = {
        "firstname": args.firstname.strip(),
        "lastname": args.lastname.strip(),
        "location": args.location.strip(),
        "current_job_title": args.title.strip(),
    }
    if not any(fields.values()):
        return bad(
            "give at least one of --firstname, --lastname, --location, --title"
        )
    if args.max_profiles < 1 or args.max_profiles > 100:
        return bad("--max-profiles must be between 1 and 100")

    query = {k: v.lower() for k, v in fields.items() if v}
    query["max_profiles"] = args.max_profiles

    run_input = dict(fields)
    run_input["max_profiles"] = args.max_profiles
    # Deliberately never asked for: this actor can also guess and "validate"
    # email addresses. Guessed addresses for identifiable people are a
    # different kind of collection; get them from a source with consent.
    run_input["include_email"] = False

    return run_search(
        args,
        cfg,
        kind="people-search",
        actor_id=cfg.actor("people-search"),
        query=query,
        run_input=run_input,
        extract_keys=extract.people_search_keys,
        summary=extract.people_search_summary,
        label=", ".join(f"{k}={v}" for k, v in query.items()),
        drop_item=extract.is_empty_people_hit,
    )


def cmd_company_search(cfg: Config, args: argparse.Namespace) -> int:
    if not args.keyword.strip():
        return bad("keyword must not be empty")
    problem = out_of_range(args, 50)
    if problem:
        return bad(problem)

    query: Dict[str, Any] = {
        "keyword": args.keyword.strip().lower(),
        "page_number": args.page,
        "limit": args.limit,
    }
    run_input: Dict[str, Any] = {
        "keyword": args.keyword.strip(),
        "page_number": args.page,
        "limit": args.limit,
    }
    for flag, key in (
        (args.location_id, "location_ids"),
        (args.industry_id, "industry_ids"),
        (args.company_size, "company_sizes"),
    ):
        values = sorted({str(v).strip() for v in (flag or []) if str(v).strip()})
        if values:
            query[key] = values
            # The actor wants comma-separated strings, not arrays.
            run_input[key] = ",".join(values)

    return run_search(
        args,
        cfg,
        kind="company-search",
        actor_id=cfg.actor("company-search"),
        query=query,
        run_input=run_input,
        extract_keys=extract.company_search_keys,
        summary=extract.company_search_summary,
        label=f"keyword {args.keyword.strip()!r} page {args.page}",
    )


def cmd_post_search(cfg: Config, args: argparse.Namespace) -> int:
    if not args.keyword.strip():
        return bad("--keyword must not be empty")
    problem = out_of_range(args, 50)
    if problem:
        return bad(problem)

    def csv(value: str) -> List[str]:
        return [part.strip() for part in (value or "").split(",") if part.strip()]

    query: Dict[str, Any] = {
        "keyword": args.keyword.strip().lower(),
        "sort_type": args.sort_type,
        "limit": args.limit,
    }
    run_input: Dict[str, Any] = {
        "keyword": args.keyword.strip(),
        "sort_type": args.sort_type,
        "page_number": args.page,
        "date_filter": args.date_filter or "",
        "limit": args.limit,
    }
    if args.total_posts:
        query["total_posts"] = args.total_posts
        run_input["total_posts"] = args.total_posts
    else:
        query["page_number"] = args.page
    if args.date_filter:
        query["date_filter"] = args.date_filter
    if args.author_job_title.strip():
        query["author_job_title"] = args.author_job_title.strip().lower()
        run_input["author_job_title"] = args.author_job_title.strip()
    for flag, key in (
        (args.company_urns, "company_urns"),
        (args.author_company_urns, "author_company_urns"),
        (args.author_industry_urns, "author_industry_urns"),
        (args.member_urns, "member_urns"),
    ):
        values = sorted(set(csv(flag)))
        if values:
            joined = ",".join(values)
            query[key] = joined
            run_input[key] = joined

    label = f"keyword {args.keyword.strip()!r}"
    label += (
        f" total_posts {args.total_posts}"
        if args.total_posts
        else f" page {args.page}"
    )

    return run_search(
        args,
        cfg,
        kind="post-search",
        actor_id=cfg.actor("post-search"),
        query=query,
        run_input=run_input,
        extract_keys=extract.post_search_keys,
        summary=extract.post_search_summary,
        label=label,
    )


def cmd_profile_posts(cfg: Config, args: argparse.Namespace) -> int:
    problem = out_of_range(args, 100)
    if problem:
        return bad(problem)
    username = extract.normalise_username(args.username)
    if not username or username == "unknown":
        return bad(f"no LinkedIn username found in {args.username!r}")

    query: Dict[str, Any] = {"username": username, "limit": args.limit}
    run_input: Dict[str, Any] = {
        "username": username,
        "page_number": args.page,
        "limit": args.limit,
    }
    if args.total_posts:
        query["total_posts"] = args.total_posts
        run_input["total_posts"] = args.total_posts
    else:
        query["page_number"] = args.page
    if args.pagination_token.strip():
        query["pagination_token"] = args.pagination_token.strip()
        run_input["pagination_token"] = args.pagination_token.strip()

    label = f"username {username!r}"
    label += (
        f" total_posts {args.total_posts}"
        if args.total_posts
        else f" page {args.page}"
    )

    return run_search(
        args,
        cfg,
        kind="profile-posts",
        actor_id=cfg.actor("profile-posts"),
        query=query,
        run_input=run_input,
        extract_keys=extract.profile_posts_keys,
        summary=extract.profile_posts_summary,
        label=label,
        item_transform=extract.flatten_profile_posts,
    )


def cmd_job_search(cfg: Config, args: argparse.Namespace) -> int:
    if not args.keywords.strip() or not args.location.strip():
        return bad("--keywords and --location must not be empty")
    problem = out_of_range(args, 1000)
    if problem:
        return bad(problem)
    query: Dict[str, Any] = {
        "keywords": args.keywords.strip().lower(),
        "location": args.location.strip().lower(),
        "page_number": args.page,
        "limit": args.limit,
    }
    run_input: Dict[str, Any] = {
        "keywords": args.keywords.strip(),
        "location": args.location.strip(),
        "page_number": args.page,
        "limit": args.limit,
    }
    for value, key in (
        (args.remote, "remote"),
        (args.sort, "sort"),
        (args.date_posted, "date_posted"),
        (args.experience_level, "experienceLevel"),
    ):
        if value:
            query[key] = value
            run_input[key] = value
    if args.easy_apply:
        query["easy_apply"] = True
        run_input["easy_apply"] = True
    if args.under_10_applicants:
        query["under_10_applicants"] = True
        run_input["under_10_applicants"] = True

    return run_search(
        args,
        cfg,
        kind="job-search",
        actor_id=cfg.actor("job-search"),
        query=query,
        run_input=run_input,
        extract_keys=extract.job_search_keys,
        summary=extract.job_search_summary,
        label=(
            f"keywords {args.keywords.strip()!r} "
            f"location {args.location.strip()!r} page {args.page}"
        ),
        item_transform=lambda items: extract.flatten_job_items(items)[0],
    )


def cmd_cache_info(cfg: Config, args: argparse.Namespace) -> int:
    with open_cache(args, cfg) as cache:
        emit(
            {
                "cache_path": cache.path,
                "enabled": cache.enabled,
                "contents": cache.stats(),
            }
        )
    return EXIT_OK


def cmd_cache_clear(cfg: Config, args: argparse.Namespace) -> int:
    with open_cache(args, cfg) as cache:
        if not cache.enabled:
            return bad("the cache is disabled, so there is nothing to clear")
        count = cache.count_matching(args.kind, args.older_than_days)
        scope = args.kind or "every kind"
        age = (
            f" older than {args.older_than_days} day(s)"
            if args.older_than_days is not None
            else ""
        )
        warn("About to delete cached rows:")
        warn(f"  file:  {cache.path}")
        warn(f"  scope: {scope}{age}")
        warn(f"  rows:  {count}")
        if not args.yes:
            warn("")
            warn("Nothing was deleted. Re-run with --yes to delete.")
            emit({"cache_path": cache.path, "would_delete": count, "deleted": 0})
            return EXIT_NOT_CONFIRMED
        deleted = cache.clear(args.kind, args.older_than_days)
        emit({"cache_path": cache.path, "deleted": deleted})
    return EXIT_OK


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

CACHE_KINDS = (
    "company",
    "profile",
    "job",
    "people-search",
    "company-search",
    "post-search",
    "profile-posts",
    "job-search",
)


def build_parser(cfg: Config) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="linkedin-enrichment",
        description=(
            "Pull public LinkedIn data through Apify actors. Sample code: read "
            "it before you run it. Cached reads run freely; anything that "
            "starts an actor run needs --yes."
        ),
    )
    parser.add_argument("--config", help="path to a linkedin-enrichment.yml")
    sub = parser.add_subparsers(dest="command", required=True)

    def common(
        p: argparse.ArgumentParser, default_age: float = DEFAULT_MAX_AGE_DAYS
    ) -> None:
        p.add_argument(
            "--yes",
            action="store_true",
            help=(
                "start the Apify run; without it the command reports what it "
                "would fetch and stops"
            ),
        )
        p.add_argument(
            "--max-age-days",
            type=float,
            default=cfg.max_age_days(default_age),
            help=f"reuse cached rows this recent (default {default_age})",
        )
        p.add_argument(
            "--no-cache",
            action="store_true",
            help="ignore the local cache entirely, for this run: no read, no write",
        )
        p.add_argument(
            "--cache-path",
            help=f"SQLite cache file (default {default_cache_path()})",
        )
        p.add_argument(
            "--output-dir",
            help="also write the raw actor output here, one JSON file per result",
        )
        p.add_argument(
            "--run-timeout",
            type=int,
            default=900,
            help="seconds to wait for an actor run (default 900)",
        )
        p.add_argument(
            "--http-timeout",
            type=int,
            default=60,
            help="seconds to wait for one API request (default 60)",
        )

    # -- detail
    p = sub.add_parser(
        "company", help="full company profiles by slug, URL or numeric id"
    )
    p.add_argument("identifiers", nargs="+")
    common(p)
    p.set_defaults(func=cmd_company)

    p = sub.add_parser(
        "profile", help="full person profiles by slug, URL or member URN"
    )
    p.add_argument("profiles", nargs="+")
    p.add_argument(
        "--scrape-company",
        action="store_true",
        help="also fetch each person's current company (slower, more credits)",
    )
    common(p)
    p.set_defaults(func=cmd_profile)

    p = sub.add_parser("job", help="full job-posting detail by id or jobs URL")
    p.add_argument("job_ids", nargs="+")
    common(p)
    p.set_defaults(func=cmd_job)

    # -- search
    p = sub.add_parser(
        "people-search", help="find people by name, title or location"
    )
    p.add_argument("--firstname", default="")
    p.add_argument("--lastname", default="")
    p.add_argument("--location", default="", help="e.g. 'London'")
    p.add_argument("--title", default="", help="current job title")
    p.add_argument(
        "--max-profiles", type=int, default=20, help="cap on hits (default 20)"
    )
    common(p)
    p.set_defaults(func=cmd_people_search)

    p = sub.add_parser("company-search", help="find companies by keyword")
    p.add_argument("keyword")
    p.add_argument("--page", type=int, default=1)
    p.add_argument("--limit", type=int, default=50)
    p.add_argument(
        "--location-id",
        action="append",
        help="LinkedIn geoId; repeatable. Read it off a filtered search URL",
    )
    p.add_argument(
        "--industry-id",
        action="append",
        help="LinkedIn industry id; repeatable",
    )
    p.add_argument(
        "--company-size",
        action="append",
        help="LinkedIn company-size bucket; repeatable",
    )
    common(p)
    p.set_defaults(func=cmd_company_search)

    p = sub.add_parser("post-search", help="find public posts by keyword")
    p.add_argument("--keyword", required=True)
    p.add_argument(
        "--sort-type", choices=("relevance", "date_posted"), default="relevance"
    )
    p.add_argument(
        "--date-filter",
        choices=("", "past-24h", "past-week", "past-month"),
        default="",
    )
    p.add_argument("--page", type=int, default=1)
    p.add_argument("--limit", type=int, default=50, help="max 50 per page")
    p.add_argument(
        "--total-posts",
        type=int,
        default=0,
        help="let the actor paginate to this many posts, instead of one page",
    )
    p.add_argument("--company-urns", default="", help="comma-separated org ids")
    p.add_argument("--author-company-urns", default="")
    p.add_argument("--author-industry-urns", default="")
    p.add_argument("--author-job-title", default="")
    p.add_argument("--member-urns", default="")
    common(p)
    p.set_defaults(func=cmd_post_search)

    p = sub.add_parser(
        "profile-posts", help="one person's post history by username"
    )
    p.add_argument("username", help="vanity slug, profile URL or 'in/<slug>'")
    p.add_argument("--page", type=int, default=1)
    p.add_argument(
        "--pagination-token",
        default="",
        help="cursor from the previous page's manifest",
    )
    p.add_argument("--limit", type=int, default=100, help="max 100 per page")
    p.add_argument("--total-posts", type=int, default=0)
    common(p, default_age=DEFAULT_POST_MAX_AGE_DAYS)
    p.set_defaults(func=cmd_profile_posts)

    p = sub.add_parser("job-search", help="find job postings by keyword")
    p.add_argument("--keywords", required=True)
    p.add_argument(
        "--location",
        required=True,
        help="country or city name, or a LinkedIn geoId",
    )
    p.add_argument(
        "--remote", choices=("", "onsite", "remote", "hybrid"), default=""
    )
    p.add_argument(
        "--experience-level",
        choices=(
            "",
            "internship",
            "entry",
            "associate",
            "mid_senior",
            "director",
            "executive",
        ),
        default="",
    )
    p.add_argument("--sort", choices=("", "relevant", "recent"), default="")
    p.add_argument(
        "--date-posted",
        choices=("", "past_24_hours", "past_week", "past_month"),
        default="",
    )
    p.add_argument("--easy-apply", action="store_true")
    p.add_argument("--under-10-applicants", action="store_true")
    p.add_argument("--page", type=int, default=1)
    p.add_argument("--limit", type=int, default=100)
    common(p)
    p.set_defaults(func=cmd_job_search)

    # -- cache housekeeping
    p = sub.add_parser("cache-info", help="what the local cache holds")
    p.add_argument("--cache-path")
    p.add_argument("--no-cache", action="store_true", help=argparse.SUPPRESS)
    p.set_defaults(func=cmd_cache_info)

    p = sub.add_parser(
        "cache-clear",
        help="delete cached rows, e.g. to honour an erasure request",
    )
    p.add_argument("--cache-path")
    p.add_argument("--kind", choices=CACHE_KINDS, help="only this kind of row")
    p.add_argument(
        "--older-than-days",
        type=float,
        help="only rows cached before this many days ago",
    )
    p.add_argument(
        "--yes", action="store_true", help="actually delete; otherwise dry run"
    )
    p.add_argument("--no-cache", action="store_true", help=argparse.SUPPRESS)
    p.set_defaults(func=cmd_cache_clear)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    # The config can change a default (--max-age-days), so it is read before
    # the real parse. A throwaway parser picks --config out of the arguments.
    pre = argparse.ArgumentParser(add_help=False)
    pre.add_argument("--config")
    known, _ = pre.parse_known_args(argv)
    cfg = load_config(known.config)

    args = build_parser(cfg).parse_args(argv)

    # The token is read only when a run is actually about to start, inside
    # make_client(). A dry run, and anything the cache can answer, needs no
    # credential at all.
    try:
        return args.func(cfg, args)
    except MissingCredential as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_ERROR
    except ApifyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_ERROR
    except KeyboardInterrupt:
        print(
            "\ninterrupted. An actor run that had already started is still "
            "running and still costing credits; abort it in the Apify console.",
            file=sys.stderr,
        )
        return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
