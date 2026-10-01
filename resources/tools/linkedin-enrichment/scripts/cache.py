#!/usr/bin/env python3
"""Local SQLite cache for Apify LinkedIn results.


Why a cache at all: every miss starts an Apify actor run, and actor runs cost
money and take tens of seconds. Re-asking for the same company twice in one
session should not bill twice.

Why SQLite rather than the warehouse table this was ported from: a sample
should not need a database server. One file on disk, stdlib only. The trade-off
is that the cache is per machine and per path, so a team does not share it.

Two shapes, mirroring the two ways these actors behave:

* **Detail cache** keyed on an identifier (a company slug, a profile slug, a
  numeric job id). Latest row per key wins.
* **Search cache** keyed on a normalised query object. A whole result page is
  stored per run, and a lookup returns the most recent complete run for that
  query, in result order.

Both are append-only. Nothing updates or deletes a row except ``clear()``.

**The rows hold personal data.** A cached LinkedIn profile is personal data
sitting on your disk, and the clock on your retention obligations does not stop
because it is "just a cache". Keep the file out of version control and out of
backups you do not control, and use ``cli.py cache-clear`` when you are done
with it.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import sqlite3
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

CACHE_PATH_ENV = "LINKEDIN_CACHE_PATH"
DEFAULT_CACHE_PATH = "linkedin-cache.db"

# (key_type, key) -> data. key_type is "id" or "slug".
DetailKey = Tuple[str, str]

SCHEMA = """
create table if not exists detail (
    id            integer primary key autoincrement,
    kind          text not null,
    key_type      text not null,
    key           text not null,
    input         text,
    actor_id      text,
    run_id        text,
    dataset_id    text,
    scraped_at    text not null,
    data          text not null
);
create index if not exists detail_lookup
    on detail (kind, key_type, key, scraped_at);

create table if not exists search (
    id            integer primary key autoincrement,
    kind          text not null,
    query_hash    text not null,
    query         text not null,
    result_index  integer not null,
    slug          text,
    linkedin_id   text,
    actor_id      text,
    run_id        text,
    dataset_id    text,
    scraped_at    text not null,
    data          text not null
);
create index if not exists search_lookup
    on search (kind, query_hash, scraped_at);
"""


def utc_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


def _cutoff(max_age_days: float) -> str:
    moment = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
        days=max_age_days
    )
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def canonical_query(query: Dict[str, Any]) -> str:
    """Stable JSON for a query object, so key order never changes the hash."""
    return json.dumps(query, sort_keys=True, separators=(",", ":"), default=str)


def query_hash(query: Dict[str, Any]) -> str:
    return hashlib.sha256(canonical_query(query).encode("utf-8")).hexdigest()


def default_cache_path() -> str:
    return os.environ.get(CACHE_PATH_ENV) or DEFAULT_CACHE_PATH


class Cache:
    """A SQLite-backed cache. Construct with ``path=None`` to disable it.

    A disabled cache answers every lookup with a miss and drops every write, so
    callers do not need an ``if self.cache`` around each call.
    """

    def __init__(self, path: Optional[str] = None) -> None:
        self.path = path
        self._conn: Optional[sqlite3.Connection] = None
        if path:
            parent = os.path.dirname(os.path.abspath(path))
            if parent and not os.path.isdir(parent):
                os.makedirs(parent, exist_ok=True)
            self._conn = sqlite3.connect(path)
            self._conn.executescript(SCHEMA)
            self._conn.commit()

    @property
    def enabled(self) -> bool:
        return self._conn is not None

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def __enter__(self) -> "Cache":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    # -- detail ------------------------------------------------------------

    def lookup_detail(
        self, kind: str, keys: Sequence[DetailKey], max_age_days: float
    ) -> Dict[DetailKey, Dict[str, Any]]:
        """Latest row per (key_type, key) for ``kind``, within max_age_days."""
        out: Dict[DetailKey, Dict[str, Any]] = {}
        if self._conn is None or not keys:
            return out
        cutoff = _cutoff(max_age_days)
        for key_type, key in keys:
            row = self._conn.execute(
                "select data from detail"
                " where kind = ? and key_type = ? and key = ? and scraped_at > ?"
                " order by scraped_at desc, id desc limit 1",
                (kind, key_type, key, cutoff),
            ).fetchone()
            if row:
                try:
                    out[(key_type, key)] = json.loads(row[0])
                except ValueError:
                    continue
        return out

    def insert_detail(self, kind: str, rows: Iterable[Dict[str, Any]]) -> None:
        """Append detail rows. Each row: key_type, key, input, actor_id,
        run_id, dataset_id, data."""
        if self._conn is None:
            return
        now = utc_now()
        payload = [
            (
                kind,
                row["key_type"],
                row["key"],
                row.get("input"),
                row.get("actor_id"),
                row.get("run_id"),
                row.get("dataset_id"),
                now,
                json.dumps(row["data"], default=str),
            )
            for row in rows
        ]
        if not payload:
            return
        self._conn.executemany(
            "insert into detail"
            " (kind, key_type, key, input, actor_id, run_id, dataset_id,"
            "  scraped_at, data)"
            " values (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            payload,
        )
        self._conn.commit()

    # -- search ------------------------------------------------------------

    def lookup_search(
        self, kind: str, query: Dict[str, Any], max_age_days: float
    ) -> Optional[List[Dict[str, Any]]]:
        """The most recent complete run for ``query``, or None on a miss.

        Returns one dict per result, in result order, carrying the stored item
        plus the run provenance.
        """
        if self._conn is None:
            return None
        cutoff = _cutoff(max_age_days)
        qhash = query_hash(query)
        latest = self._conn.execute(
            "select run_id, max(scraped_at) as t from search"
            " where kind = ? and query_hash = ? and scraped_at > ?"
            " group by run_id order by t desc limit 1",
            (kind, qhash, cutoff),
        ).fetchone()
        if not latest:
            return None
        run_id = latest[0]
        rows = self._conn.execute(
            "select data, slug, linkedin_id, scraped_at, run_id, dataset_id"
            " from search"
            " where kind = ? and query_hash = ?"
            "   and (run_id = ? or (? is null and run_id is null))"
            " order by result_index",
            (kind, qhash, run_id, run_id),
        ).fetchall()
        if not rows:
            return None
        out = []
        for data, slug, linkedin_id, scraped_at, rid, dataset_id in rows:
            try:
                item = json.loads(data)
            except ValueError:
                continue
            out.append(
                {
                    "data": item,
                    "slug": slug,
                    "linkedin_id": linkedin_id,
                    "scraped_at": scraped_at,
                    "run_id": rid,
                    "dataset_id": dataset_id,
                }
            )
        return out or None

    def insert_search(
        self,
        kind: str,
        query: Dict[str, Any],
        actor_id: Optional[str],
        run_id: Optional[str],
        dataset_id: Optional[str],
        items: Sequence[Dict[str, Any]],
        extract_keys: Callable[[Dict[str, Any]], Tuple[Optional[str], Optional[str]]],
    ) -> None:
        if self._conn is None or not items:
            return
        now = utc_now()
        qhash = query_hash(query)
        qjson = canonical_query(query)
        payload = []
        for index, item in enumerate(items):
            slug, linkedin_id = extract_keys(item)
            payload.append(
                (
                    kind,
                    qhash,
                    qjson,
                    index,
                    slug,
                    linkedin_id,
                    actor_id,
                    run_id,
                    dataset_id,
                    now,
                    json.dumps(item, default=str),
                )
            )
        self._conn.executemany(
            "insert into search"
            " (kind, query_hash, query, result_index, slug, linkedin_id,"
            "  actor_id, run_id, dataset_id, scraped_at, data)"
            " values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            payload,
        )
        self._conn.commit()

    # -- housekeeping ------------------------------------------------------

    def stats(self) -> List[Dict[str, Any]]:
        if self._conn is None:
            return []
        out: List[Dict[str, Any]] = []
        for table in ("detail", "search"):
            rows = self._conn.execute(
                f"select kind, count(*), min(scraped_at), max(scraped_at)"
                f" from {table} group by kind order by kind"
            ).fetchall()
            for kind, count, oldest, newest in rows:
                out.append(
                    {
                        "table": table,
                        "kind": kind,
                        "rows": count,
                        "oldest": oldest,
                        "newest": newest,
                    }
                )
        return out

    def count_matching(
        self, kind: Optional[str] = None, older_than_days: Optional[float] = None
    ) -> int:
        return self._affected(kind, older_than_days, delete=False)

    def clear(
        self, kind: Optional[str] = None, older_than_days: Optional[float] = None
    ) -> int:
        """Delete cached rows. Returns the number removed."""
        return self._affected(kind, older_than_days, delete=True)

    def _affected(
        self,
        kind: Optional[str],
        older_than_days: Optional[float],
        delete: bool,
    ) -> int:
        if self._conn is None:
            return 0
        where = []
        params: List[Any] = []
        if kind:
            where.append("kind = ?")
            params.append(kind)
        if older_than_days is not None:
            where.append("scraped_at <= ?")
            params.append(_cutoff(older_than_days))
        clause = (" where " + " and ".join(where)) if where else ""
        total = 0
        for table in ("detail", "search"):
            if delete:
                cur = self._conn.execute(f"delete from {table}{clause}", params)
                total += cur.rowcount or 0
            else:
                row = self._conn.execute(
                    f"select count(*) from {table}{clause}", params
                ).fetchone()
                total += row[0] if row else 0
        if delete:
            self._conn.commit()
            self._conn.execute("vacuum")
        return total
