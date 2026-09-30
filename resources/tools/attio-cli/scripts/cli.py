#!/usr/bin/env python3
"""Command-line front end for the Attio API v2.

Example code, provided as-is. Not part of the Bruin platform.

    python3 cli.py objects
    python3 cli.py search companies "acme"
    python3 cli.py update companies <record-id> '{"industry":"Software"}' --yes

Reads are unrestricted. Every write prints the exact change first and then stops
unless ``--yes`` is given, so a command can always be run once to see what it
would do.

The API key comes from the ATTIO_API_KEY environment variable only; see
attio_client.py.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional

try:  # Run as a module (python3 -m scripts.cli) or as a plain script.
    from .attio_client import AttioClient, AttioError, MissingCredential
except ImportError:  # pragma: no cover - depends on invocation style
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from attio_client import AttioClient, AttioError, MissingCredential

EXIT_OK = 0
EXIT_ERROR = 1
# Not 2: argparse exits 2 on a usage error, and the two must not be confused.
EXIT_NOT_CONFIRMED = 3

CONFIG_ENV = "ATTIO_CLI_CONFIG"
CONFIG_FILENAMES = ("attio-cli.yml", "attio-cli.yaml", "attio-cli.json")


# ---------------------------------------------------------------------------
# Configuration
#
# Nothing about a workspace's schema is hardcoded. Object slugs, list slugs and
# the attribute a "search" matches on differ per workspace, so they live in an
# optional config file that maps your own aliases onto your own slugs. With no
# config file the CLI still works: whatever you type is used as the slug.
# ---------------------------------------------------------------------------


class Config:
    def __init__(self, raw: Optional[Dict[str, Any]] = None, path: Optional[str] = None) -> None:
        raw = raw or {}
        self.path = path
        self.defaults: Dict[str, Any] = raw.get("defaults") or {}
        self.objects: Dict[str, Any] = raw.get("objects") or {}
        self.lists: Dict[str, Any] = raw.get("lists") or {}

    @property
    def default_limit(self) -> int:
        try:
            return int(self.defaults.get("limit", 25))
        except (TypeError, ValueError):
            return 25

    def object_entry(self, alias: str) -> Dict[str, Any]:
        entry = self.objects.get(alias)
        if isinstance(entry, str):  # shorthand: `company: companies`
            return {"slug": entry}
        return entry or {}

    def list_entry(self, alias: str) -> Dict[str, Any]:
        entry = self.lists.get(alias)
        if isinstance(entry, str):
            return {"slug": entry}
        return entry or {}

    def object_slug(self, alias: str) -> str:
        return self.object_entry(alias).get("slug", alias)

    def list_slug(self, alias: str) -> str:
        return self.list_entry(alias).get("slug", alias)

    def search_attribute(self, alias: str) -> str:
        # `name` is the usual text attribute on Attio's standard objects, but a
        # custom object may not have one. Override per object in the config.
        return self.object_entry(alias).get("search_attribute", "name")

    def display_attributes(self, alias: str) -> List[str]:
        display = self.object_entry(alias).get("display")
        return list(display) if isinstance(display, list) else []


def load_config(explicit_path: Optional[str]) -> Config:
    """Load config from --config, then $ATTIO_CLI_CONFIG, then the cwd."""
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
                import yaml  # imported lazily so PyYAML is only needed for YAML config
            except ImportError:
                raise SystemExit(
                    "PyYAML is required to read a YAML config file: pip install PyYAML "
                    "(or use a .json config)"
                )
            raw = yaml.safe_load(handle) or {}
    if not isinstance(raw, dict):
        raise SystemExit(f"config file {path} must contain a mapping at the top level")
    return Config(raw, path=path)


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


def print_json(data: Any) -> None:
    print(json.dumps(data, indent=2, default=str, ensure_ascii=False))


def _flatten_value(value: Any) -> str:
    """Best-effort one-line rendering of one Attio attribute value.

    Attio returns every attribute as a list of versioned value objects whose
    shape depends on the attribute type. This covers the common shapes and
    falls back to compact JSON, so it is a convenience for eyeballing results,
    never something to parse. Use `--format json` when the exact shape matters.
    """
    if isinstance(value, list):
        return ", ".join(_flatten_value(item) for item in value if item is not None)
    if isinstance(value, dict):
        for key in (
            "value",
            "full_name",
            "domain",
            "email_address",
            "phone_number",
            "title",
            "status",
            "option",
            "target_record_id",
            "referenced_actor_id",
        ):
            if key in value:
                inner = value[key]
                return _flatten_value(inner) if isinstance(inner, (dict, list)) else str(inner)
        return json.dumps(value, default=str)[:120]
    return "" if value is None else str(value)


def print_records_table(records: List[Dict[str, Any]], attributes: List[str]) -> None:
    """Print id plus the configured display attributes, one record per line."""
    if not records:
        print("(no results)")
        return
    for record in records:
        record_id = (record.get("id") or {}).get("record_id", "")
        values = record.get("values") or {}
        if attributes:
            shown = [_flatten_value(values.get(attr)) for attr in attributes]
        else:
            # No display config: show whatever the first few attributes are.
            shown = [f"{k}={_flatten_value(v)}" for k, v in list(values.items())[:3]]
        print("  ".join([record_id] + [s for s in shown if s]))


def print_definitions(items: List[Dict[str, Any]], fields: List[str]) -> None:
    for item in items:
        parts = []
        for field in fields:
            parts.append(str(item.get(field, "") or ""))
        print("  ".join(p.ljust(34) if i == 0 else p for i, p in enumerate(parts)).rstrip())


# ---------------------------------------------------------------------------
# Write gate
# ---------------------------------------------------------------------------


def confirm(args: argparse.Namespace, summary: str, payload: Any = None) -> bool:
    """Show the change, then require --yes before it happens.

    Returns False when the caller should stop. Printing first means the same
    command without --yes is a safe dry run.
    """
    print("About to change Attio:")
    print(f"  {summary}")
    if payload is not None:
        for line in json.dumps(payload, indent=2, default=str, ensure_ascii=False).splitlines():
            print(f"  {line}")
    if getattr(args, "yes", False):
        return True
    print("\nNothing was changed. Re-run the same command with --yes to apply it.")
    return False


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def _json_arg(raw: Optional[str], what: str) -> Optional[Any]:
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{what} is not valid JSON: {exc}")


def cmd_objects(client: AttioClient, cfg: Config, args: argparse.Namespace) -> int:
    data = client.list_objects()
    if args.format == "json":
        print_json(data)
    else:
        print_definitions(data, ["api_slug", "singular_noun", "plural_noun"])
    return EXIT_OK


def cmd_attrs(client: AttioClient, cfg: Config, args: argparse.Namespace) -> int:
    data = client.list_attributes(cfg.object_slug(args.object), limit=args.limit)
    if args.format == "json":
        print_json(data)
    else:
        print_definitions(data, ["api_slug", "type", "title"])
    return EXIT_OK


def cmd_lists(client: AttioClient, cfg: Config, args: argparse.Namespace) -> int:
    data = client.list_lists(limit=args.limit)
    if args.format == "json":
        print_json(data)
    else:
        print_definitions(data, ["api_slug", "name"])
    return EXIT_OK


def cmd_list_attrs(client: AttioClient, cfg: Config, args: argparse.Namespace) -> int:
    data = client.list_list_attributes(cfg.list_slug(args.list))
    if args.format == "json":
        print_json(data)
    else:
        print_definitions(data, ["api_slug", "type", "title"])
    return EXIT_OK


def cmd_search(client: AttioClient, cfg: Config, args: argparse.Namespace) -> int:
    attribute = args.attribute or cfg.search_attribute(args.object)
    records = client.search_records(
        cfg.object_slug(args.object),
        args.query,
        search_attribute=attribute,
        limit=args.limit,
        offset=args.offset,
    )
    if args.format == "json":
        print_json(records)
    else:
        print_records_table(records, cfg.display_attributes(args.object))
    return EXIT_OK


def cmd_query(client: AttioClient, cfg: Config, args: argparse.Namespace) -> int:
    filter_ = _json_arg(args.filter, "--filter")
    sorts = _json_arg(args.sort, "--sort")
    slug = cfg.object_slug(args.object)
    if args.all:
        records = list(client.iter_records(slug, filter_, sorts, max_records=args.max))
    else:
        records = client.query_records(slug, filter_, sorts, limit=args.limit, offset=args.offset)
    if args.format == "json":
        print_json(records)
    else:
        print_records_table(records, cfg.display_attributes(args.object))
    return EXIT_OK


def cmd_get(client: AttioClient, cfg: Config, args: argparse.Namespace) -> int:
    print_json(client.get_record(cfg.object_slug(args.object), args.record_id))
    return EXIT_OK


def cmd_entries(client: AttioClient, cfg: Config, args: argparse.Namespace) -> int:
    entries = client.query_entries(
        cfg.list_slug(args.list),
        filter=_json_arg(args.filter, "--filter"),
        sorts=_json_arg(args.sort, "--sort"),
        limit=args.limit,
        offset=args.offset,
    )
    print_json(entries)
    return EXIT_OK


def cmd_create(client: AttioClient, cfg: Config, args: argparse.Namespace) -> int:
    slug = cfg.object_slug(args.object)
    values = _json_arg(args.values, "values")
    if not confirm(args, f"create a new '{slug}' record with these values", values):
        return EXIT_NOT_CONFIRMED
    print_json(client.create_record(slug, values))
    return EXIT_OK


def cmd_update(client: AttioClient, cfg: Config, args: argparse.Namespace) -> int:
    slug = cfg.object_slug(args.object)
    values = _json_arg(args.values, "values")
    current = None
    try:
        current = client.get_record(slug, args.record_id)
    except AttioError:
        pass  # Preview is a courtesy; a failure here should not block the update.
    if current:
        existing = current.get("values") or {}
        print("Current values for the attributes being written:")
        for key in values:
            print(f"  {key}: {_flatten_value(existing.get(key))}")
    if not confirm(args, f"overwrite these attributes on {slug}/{args.record_id}", values):
        return EXIT_NOT_CONFIRMED
    print_json(client.update_record(slug, args.record_id, values))
    return EXIT_OK


def cmd_upsert(client: AttioClient, cfg: Config, args: argparse.Namespace) -> int:
    slug = cfg.object_slug(args.object)
    values = _json_arg(args.values, "values")
    summary = (
        f"create or overwrite a '{slug}' record, matched on "
        f"'{args.matching_attribute}', with these values"
    )
    if not confirm(args, summary, values):
        return EXIT_NOT_CONFIRMED
    print_json(client.assert_record(slug, args.matching_attribute, values))
    return EXIT_OK


def cmd_delete(client: AttioClient, cfg: Config, args: argparse.Namespace) -> int:
    slug = cfg.object_slug(args.object)
    preview: Any = None
    try:
        preview = client.get_record(slug, args.record_id)
    except AttioError:
        pass
    if preview:
        print("Record to delete:")
        print_records_table([preview], cfg.display_attributes(args.object))
    summary = f"permanently delete {slug}/{args.record_id}. Attio deletion cannot be undone."
    if not confirm(args, summary):
        return EXIT_NOT_CONFIRMED
    client.delete_record(slug, args.record_id)
    print(f"Deleted {slug}/{args.record_id}")
    return EXIT_OK


def cmd_update_entry(client: AttioClient, cfg: Config, args: argparse.Namespace) -> int:
    slug = cfg.list_slug(args.list)
    values = _json_arg(args.values, "values")
    if not confirm(args, f"overwrite entry values on list '{slug}', entry {args.entry_id}", values):
        return EXIT_NOT_CONFIRMED
    print_json(client.update_list_entry(slug, args.entry_id, values))
    return EXIT_OK


def cmd_add_to_list(client: AttioClient, cfg: Config, args: argparse.Namespace) -> int:
    slug = cfg.list_slug(args.list)
    object_slug = cfg.object_slug(args.object)
    values = _json_arg(args.values, "--values")
    summary = f"add {object_slug}/{args.record_id} to list '{slug}'"
    if not confirm(args, summary, values):
        return EXIT_NOT_CONFIRMED
    print_json(client.add_to_list(slug, object_slug, args.record_id, entry_values=values))
    return EXIT_OK


def cmd_delete_entry(client: AttioClient, cfg: Config, args: argparse.Namespace) -> int:
    slug = cfg.list_slug(args.list)
    if not confirm(args, f"remove entry {args.entry_id} from list '{slug}'"):
        return EXIT_NOT_CONFIRMED
    client.delete_list_entry(slug, args.entry_id)
    print(f"Removed entry {args.entry_id} from list {slug}")
    return EXIT_OK


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


def build_parser(default_limit: int) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="attio-cli",
        description="Read and, with --yes, write Attio CRM data. Sample code: read it before you run it.",
    )
    parser.add_argument("--config", help="path to an attio-cli.yml / .json config file")
    parser.add_argument(
        "--format", choices=("json", "table"), default="json", help="output format (default: json)"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # --format is accepted after the subcommand too. SUPPRESS keeps the
    # top-level value unless it is given again here.
    fmt = argparse.ArgumentParser(add_help=False)
    fmt.add_argument(
        "--format", choices=("json", "table"), default=argparse.SUPPRESS, help="output format (default: json)"
    )

    def add(name: str, **kwargs: Any) -> argparse.ArgumentParser:
        return sub.add_parser(name, parents=[fmt], **kwargs)

    def add_write_flag(p: argparse.ArgumentParser) -> None:
        p.add_argument(
            "--yes",
            action="store_true",
            help="apply the change; without it the command only prints what it would do",
        )

    # -- reads
    p = add("objects", help="list the objects in the workspace")
    p.set_defaults(func=cmd_objects)

    p = add("attrs", help="list attribute definitions for an object")
    p.add_argument("object", help="object slug or config alias")
    p.add_argument("--limit", type=int, default=100)
    p.set_defaults(func=cmd_attrs)

    p = add("lists", help="list the lists in the workspace")
    p.add_argument("--limit", type=int, default=100)
    p.set_defaults(func=cmd_lists)

    p = add("list-attrs", help="list attribute definitions for a list")
    p.add_argument("list", help="list slug or config alias")
    p.set_defaults(func=cmd_list_attrs)

    p = add("search", help="substring search on one attribute")
    p.add_argument("object", help="object slug or config alias")
    p.add_argument("query")
    p.add_argument("--attribute", help="attribute to match on (default: from config, else 'name')")
    p.add_argument("--limit", type=int, default=default_limit)
    p.add_argument("--offset", type=int, default=0)
    p.set_defaults(func=cmd_search)

    p = add("query", help="query records with an Attio filter")
    p.add_argument("object", help="object slug or config alias")
    p.add_argument("-f", "--filter", help="filter JSON, e.g. '{\"name\":{\"$contains\":\"acme\"}}'")
    p.add_argument("-s", "--sort", help="sorts JSON")
    p.add_argument("--limit", type=int, default=default_limit)
    p.add_argument("--offset", type=int, default=0)
    p.add_argument("--all", action="store_true", help="page through all matches")
    p.add_argument("--max", type=int, default=1000, help="cap for --all (default: 1000)")
    p.set_defaults(func=cmd_query)

    p = add("get", help="fetch one record by id")
    p.add_argument("object", help="object slug or config alias")
    p.add_argument("record_id")
    p.set_defaults(func=cmd_get)

    p = add("entries", help="query entries in a list")
    p.add_argument("list", help="list slug or config alias")
    p.add_argument("-f", "--filter", help="filter JSON")
    p.add_argument("-s", "--sort", help="sorts JSON")
    p.add_argument("--limit", type=int, default=default_limit)
    p.add_argument("--offset", type=int, default=0)
    p.set_defaults(func=cmd_entries)

    # -- writes, all gated behind --yes
    p = add("create", help="create a record (WRITE)")
    p.add_argument("object")
    p.add_argument("values", help="attribute values as JSON")
    add_write_flag(p)
    p.set_defaults(func=cmd_create)

    p = add("update", help="overwrite attributes on a record (WRITE)")
    p.add_argument("object")
    p.add_argument("record_id")
    p.add_argument("values", help="attribute values as JSON")
    add_write_flag(p)
    p.set_defaults(func=cmd_update)

    p = add("upsert", help="create or update, matched on an attribute (WRITE)")
    p.add_argument("object")
    p.add_argument("matching_attribute", help="unique attribute slug to match on")
    p.add_argument("values", help="attribute values as JSON")
    add_write_flag(p)
    p.set_defaults(func=cmd_upsert)

    p = add("delete", help="delete a record, irreversibly (WRITE)")
    p.add_argument("object")
    p.add_argument("record_id")
    add_write_flag(p)
    p.set_defaults(func=cmd_delete)

    p = add("update-entry", help="overwrite values on a list entry (WRITE)")
    p.add_argument("list")
    p.add_argument("entry_id")
    p.add_argument("values", help="entry values as JSON")
    add_write_flag(p)
    p.set_defaults(func=cmd_update_entry)

    p = add("add-to-list", help="add an existing record to a list (WRITE)")
    p.add_argument("list")
    p.add_argument("object", help="object slug or alias the record belongs to")
    p.add_argument("record_id")
    p.add_argument("-v", "--values", help="entry values as JSON")
    add_write_flag(p)
    p.set_defaults(func=cmd_add_to_list)

    p = add("delete-entry", help="remove an entry from a list (WRITE)")
    p.add_argument("list")
    p.add_argument("entry_id")
    add_write_flag(p)
    p.set_defaults(func=cmd_delete_entry)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    # The config can change a default (--limit), so it is read before the real
    # parse. A throwaway parser picks --config out without failing on the rest.
    pre = argparse.ArgumentParser(add_help=False)
    pre.add_argument("--config")
    known, _ = pre.parse_known_args(argv)
    cfg = load_config(known.config)

    args = build_parser(cfg.default_limit).parse_args(argv)

    try:
        client = AttioClient()
    except MissingCredential as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_ERROR

    try:
        return args.func(client, cfg, args)
    except AttioError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
