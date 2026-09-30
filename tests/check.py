#!/usr/bin/env python3
"""Validate the catalogue.

One script, no dependencies outside the standard library. It checks the things
that actually break in a repository like this: a skill that will not load, a
resource nobody can find because it was never added to the index, a link to a
file that moved, and a file nobody has checked against upstream in six months.

    ./tests/check.py

Exit 0 if everything passes. Exit 1 on any error. Warnings never fail the run.
"""

from __future__ import annotations

import datetime
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
RESOURCES = REPO / "resources"
README = REPO / "README.md"

VALID_STATUS = {"stable", "experimental", "community"}
VALID_RISK = {"read-only", "approval-required", "write-capable"}

# A skill that outgrows this stops being loaded whole, which is the entire
# reason for the SKILL.md plus sibling-file split.
MAX_SKILL_WORDS = 2000

# Upstream moves. A file nobody has rechecked in this long is a hint, not a fact.
STALE_DAYS = 180

# These must never be committed, whatever they contain.
FORBIDDEN = {".bruin.yml", ".bruin.yaml", ".env", "credentials.json", "service-account.json"}

# Identifiers that are not secrets, so a credential scanner ignores them, but
# that leak the internals of whoever wrote the resource. These reach a public
# repository easily because they look like ordinary example values.
INTERNAL_PATTERNS: list[tuple[str, str]] = [
    ("Slack channel or team ID", r"\b[CGDT]0[A-Z0-9]{8,}\b"),
    ("ULID, often a project or pipeline ID", r"\b01[0-9a-hjkmnp-tv-z]{24}\b"),
    ("Google Sheet or Drive file ID", r"/d/[A-Za-z0-9_-]{30,}"),
    ("internal Bruin email domain", r"@getbruin\.com"),
    ("GCP service account", r"[a-z0-9-]+@[a-z0-9-]+\.iam\.gserviceaccount\.com"),
]

# Lines carrying this marker are exempt, for the rare case where such a string
# genuinely belongs in documentation.
ALLOW_MARKER = "check: allow"

errors: list[str] = []
warnings: list[str] = []


def err(where: pathlib.Path | str, msg: str) -> None:
    loc = where.relative_to(REPO) if isinstance(where, pathlib.Path) else where
    errors.append(f"{loc}: {msg}")


def warn(where: pathlib.Path | str, msg: str) -> None:
    loc = where.relative_to(REPO) if isinstance(where, pathlib.Path) else where
    warnings.append(f"{loc}: {msg}")


def parse_frontmatter(text: str) -> tuple[dict[str, str], str] | None:
    """Minimal YAML frontmatter reader. Only flat `key: value` is valid here,
    which is deliberate: extra structure is what breaks strict skill loaders."""
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---\n", 4)
    if end == -1:
        return None
    meta: dict[str, str] = {}
    key = None
    for line in text[4:end].splitlines():
        if re.match(r"^[a-z_]+:", line):
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip()
        elif key and line.startswith(" "):
            meta[key] += " " + line.strip()
    return meta, text[end + 5 :]


def check_skill(path: pathlib.Path) -> None:
    text = path.read_text(encoding="utf-8")
    parsed = parse_frontmatter(text)
    if parsed is None:
        err(path, "no YAML frontmatter")
        return
    meta, body = parsed

    if set(meta) != {"name", "description"}:
        err(path, f"frontmatter must be exactly name and description, found {sorted(meta)}")

    name = meta.get("name", "")
    if name != path.parent.name:
        err(path, f"name '{name}' does not match folder '{path.parent.name}'")

    desc = meta.get("description", "")
    if not desc.startswith("Use when"):
        err(path, "description must start with 'Use when' so an agent can route on it")
    if not 60 <= len(desc) <= 600:
        err(path, f"description is {len(desc)} chars, keep it between 60 and 600")

    words = len(body.split())
    if words > MAX_SKILL_WORDS:
        warn(path, f"{words} words; move depth into a sibling file so it still loads whole")

    m = re.search(r"^\*\*Status:\*\* (\S+) · \*\*Risk:\*\* (\S+)$", body, re.M)
    if not m:
        err(path, "missing a '**Status:** x · **Risk:** y' line")
    else:
        if m.group(1) not in VALID_STATUS:
            err(path, f"status '{m.group(1)}' not one of {sorted(VALID_STATUS)}")
        if m.group(2) not in VALID_RISK:
            err(path, f"risk '{m.group(2)}' not one of {sorted(VALID_RISK)}")


# A resource that drives a Bruin tool must defer to Bruin's documentation,
# because the tool moves and the file does not. A resource that drives no Bruin
# tool has nothing there to defer to, and carrying the note anyway is noise.
BRUIN_MARKERS = ("getbruin.com", "bruin init", "bruin run", "bruin query",
                 "bruin ai skills", "bruin connections", "bruin cloud",
                 "bruin validate", "bruin mcp", "ingestr")


def uses_bruin_tool(text: str) -> bool:
    """Two or more distinct markers. A single passing mention is usually a
    pointer elsewhere ("contribute upstream, run `bruin init --help`"), and
    demanding a Bruin-docs note on such a file would assert something untrue."""
    return sum(marker in text for marker in BRUIN_MARKERS) >= 2


def check_upstream_note(path: pathlib.Path) -> None:
    text = path.read_text(encoding="utf-8")
    has_note = "Upstream documentation wins" in text
    drives_bruin = uses_bruin_tool(text)

    if drives_bruin and not has_note:
        err(path, "drives a Bruin tool, so it needs the 'Upstream "
                  "documentation wins' note with a version and date")
        return

    # Not a Bruin resource. The note is not required, and carrying a Bruin-docs
    # note here would point a reader at documentation that does not govern it.
    if not drives_bruin and has_note and "getbruin.com" in text:
        err(path, "has a Bruin upstream note but does not drive a Bruin tool")

    # The date may wrap onto the next line of a blockquote.
    m = re.search(r"checked\s+(?:>\s*)?(\d{4}-\d{2}-\d{2})", text, re.IGNORECASE)
    if not m:
        # A note without a date can never go stale, which defeats the point of
        # having it. If a file must defer to upstream, it must say when it last
        # agreed with upstream.
        if has_note:
            err(path, "has an upstream note but no 'checked YYYY-MM-DD' date, "
                      "so it can never be reported as stale")
        return
    if drives_bruin and not re.search(r"\bv\d+\.\d+\.\d+\b", text):
        err(path, "drives a Bruin tool, so its upstream note needs the Bruin "
                  "CLI version it was checked against, e.g. `v0.11.765`")
    checked = datetime.date.fromisoformat(m.group(1))
    today = datetime.date.today()
    if checked > today:
        err(path, f"checked date {checked} is in the future")
    elif (today - checked).days > STALE_DAYS:
        warn(path, f"last checked {(today - checked).days} days ago, re-verify against upstream")


def check_index() -> None:
    """Every resource must be findable from the README, and the README must not
    promise a resource that is not there. This is the failure people actually
    hit: a skill is added and nobody updates the index."""
    listed = set(re.findall(r"\]\(resources/([a-z0-9/-]+)/\)", README.read_text(encoding="utf-8")))
    actual = {
        str(p.parent.relative_to(RESOURCES)) for p in RESOURCES.rglob("SKILL.md")
    }
    for missing in sorted(actual - listed):
        err("README.md", f"resource 'resources/{missing}' is not listed in the index")
    for phantom in sorted(listed - actual):
        if not (RESOURCES / phantom).is_dir():
            err("README.md", f"index links to 'resources/{phantom}', which does not exist")


def check_links() -> None:
    """Local links only. An external link check fails for reasons unrelated to
    the change under review, and a build that is red for unrelated reasons
    stops being read."""
    for path in sorted(REPO.rglob("*.md")):
        if any(part in {".git", ".context"} for part in path.parts):
            continue
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for target in re.findall(r"\[[^\]]*\]\(([^)\s]+)\)", line):
                if target.startswith(("http", "#", "mailto:")):
                    continue
                if not (path.parent / target.split("#")[0]).exists():
                    err(path, f"line {line_no}: broken link to '{target}'")


def check_internal_identifiers() -> None:
    """Catch internal identifiers that gitleaks will not, because they are not
    secrets. A hardcoded Slack channel or project ULID is how a resource ported
    out of a private repo quietly carries its old home with it."""
    for path in sorted(REPO.rglob("*")):
        if not path.is_file() or any(p in {".git", ".context"} for p in path.parts):
            continue
        if path.suffix not in {".md", ".py", ".yml", ".yaml", ".json", ".toml", ".sh", ".txt"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for line_no, line in enumerate(text.splitlines(), 1):
            if ALLOW_MARKER in line:
                continue
            for label, pattern in INTERNAL_PATTERNS:
                m = re.search(pattern, line)
                if m:
                    err(path, f"line {line_no}: {label} ('{m.group(0)[:40]}')")


def check_forbidden_files() -> None:
    for path in REPO.rglob("*"):
        if ".git" in path.parts or not path.is_file():
            continue
        if path.name in FORBIDDEN:
            err(path, "this file must never be committed")


def main() -> int:
    skills = sorted(RESOURCES.rglob("SKILL.md"))
    if not skills:
        print("error: no skills found under resources/")
        return 1

    for skill in skills:
        check_skill(skill)
    for doc in sorted(RESOURCES.rglob("*.md")):
        check_upstream_note(doc)

    check_index()
    check_links()
    check_internal_identifiers()
    check_forbidden_files()

    docs = len(list(RESOURCES.rglob("*.md")))
    print(f"checked {len(skills)} skill(s) across {docs} resource file(s)")

    for message in warnings:
        print(f"  warn   {message}")
    for message in errors:
        print(f"  ERROR  {message}")

    if errors:
        print(f"\n{len(errors)} error(s).")
        return 1
    print(f"ok ({len(warnings)} warning(s)).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
