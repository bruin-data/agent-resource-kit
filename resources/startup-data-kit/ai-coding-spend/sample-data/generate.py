#!/usr/bin/env python3
"""Regenerate the fake Claude Code and Cursor usage CSVs in this folder.

Sample code: read it before you run it.

Every value is invented: the people, the organisation, the token counts and the
per-token rates. Nothing is derived from real usage or real pricing. The seed is
fixed, so the output is identical on every run.

    python3 generate.py

Standard library only.
"""

from __future__ import annotations

import csv
import datetime
import json
import pathlib
import random

HERE = pathlib.Path(__file__).resolve().parent
RNG = random.Random(6682)

START = datetime.date(2026, 9, 14)
DAYS = 14

ORG_ID = "org_example_demo"

# Fictional people on the reserved example.com domain. "claude" and "cursor"
# say which tool each uses; "weight" scales how heavily.
PEOPLE = [
    {"email": "alex@example.com", "claude": True, "cursor": True, "weight": 1.6},
    {"email": "blair@example.com", "claude": True, "cursor": False, "weight": 1.2},
    {"email": "casey@example.com", "claude": False, "cursor": True, "weight": 1.0},
    {"email": "devon@example.com", "claude": True, "cursor": True, "weight": 0.8},
    {"email": "emery@example.com", "claude": True, "cursor": False, "weight": 0.4},
    {"email": "finley@example.com", "claude": False, "cursor": True, "weight": 0.7},
    # Cursor reports this person with different casing. The template lowercases
    # emails, so both platforms still join to one user.
    {"email": "sam.rivera@example.com", "cursor_email": "Sam.Rivera@Example.com",
     "claude": True, "cursor": True, "weight": 1.1},
]

# A CI key, so the data shows an API-key actor counted alongside people.
API_KEY = "ci-review-bot"

# Invented rates in US cents per million tokens: input, output, cache read,
# cache write. Not any vendor's price list.
CLAUDE_RATES = {
    "claude-sonnet-demo": (300, 1500, 30, 375),
    "claude-opus-demo": (1500, 7500, 150, 1875),
    "claude-haiku-demo": (100, 500, 10, 125),
}
CURSOR_MODELS = ["cursor-fast-demo", "cursor-agent-demo", "cursor-max-demo"]
CURSOR_RATES = {
    "cursor-fast-demo": (100, 400, 10, 125),
    "cursor-agent-demo": (300, 1500, 30, 375),
    "cursor-max-demo": (1200, 6000, 120, 1500),
}


def cents(rates: tuple[int, int, int, int], tokens: tuple[int, int, int, int]) -> float:
    return round(sum(r * t for r, t in zip(rates, tokens)) / 1_000_000, 4)


def tokens(scale: float) -> tuple[int, int, int, int]:
    inp = int(RNG.uniform(40_000, 120_000) * scale)
    out = int(inp * RNG.uniform(0.15, 0.35))
    cache_read = int(inp * RNG.uniform(4, 9))
    cache_write = int(inp * RNG.uniform(0.3, 0.8))
    return inp, out, cache_read, cache_write


def epoch_ms(day: datetime.date, hour: int = 0, minute: int = 0) -> int:
    moment = datetime.datetime(day.year, day.month, day.day, hour, minute,
                               tzinfo=datetime.timezone.utc)
    return int(moment.timestamp() * 1000)


def write(name: str, header: list[str], rows: list[list[object]]) -> None:
    with (HERE / name).open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def main() -> None:
    claude_rows: list[list[object]] = []
    cursor_daily: list[list[object]] = []
    cursor_events: list[list[object]] = []

    for offset in range(DAYS):
        day = START + datetime.timedelta(days=offset)
        weekend = day.weekday() >= 5
        second_week = offset >= 7

        for person in PEOPLE:
            active_chance = 0.25 if weekend else 0.9
            scale = person["weight"] * (0.4 if weekend else 1.0)

            if person["claude"] and RNG.random() < active_chance:
                # In the second week devon moves most work to the expensive
                # model, so estimated cost jumps while tokens barely move.
                if person["email"] == "devon@example.com" and second_week:
                    models = "claude-opus-demo,claude-sonnet-demo"
                    rate = CLAUDE_RATES["claude-opus-demo"]
                elif RNG.random() < 0.15:
                    models = "claude-haiku-demo"
                    rate = CLAUDE_RATES["claude-haiku-demo"]
                else:
                    models = "claude-sonnet-demo"
                    rate = CLAUDE_RATES["claude-sonnet-demo"]
                terminals = ["vscode"] if RNG.random() < 0.6 else ["vscode", "iTerm.app"]
                for terminal in terminals:
                    t = tokens(scale / len(terminals))
                    added = int(RNG.uniform(80, 600) * scale)
                    claude_rows.append([
                        day.isoformat(), "user_actor", person["email"], ORG_ID,
                        "subscription", terminal, RNG.randint(1, 5),
                        added, int(added * RNG.uniform(0.2, 0.6)),
                        RNG.randint(0, 3), RNG.randint(0, 1), *t, cents(rate, t), models,
                    ])

            if person["cursor"]:
                active = RNG.random() < active_chance
                email = person.get("cursor_email", person["email"])
                composer = RNG.randint(2, 15) if active else 0
                chat = RNG.randint(1, 10) if active else 0
                agent = RNG.randint(0, 12) if active else 0
                accepts = RNG.randint(5, 40) if active else 0
                rejects = RNG.randint(1, 15) if active else 0
                tabs_shown = RNG.randint(50, 400) if active else 0
                total_added = int(RNG.uniform(100, 900) * scale) if active else 0
                model = RNG.choice(CURSOR_MODELS[:2]) if active else ""
                cursor_daily.append([
                    epoch_ms(day), email, str(active).lower(),
                    total_added, int(total_added * 0.4),
                    int(total_added * 0.6), int(total_added * 0.2),
                    accepts + rejects, accepts, rejects,
                    tabs_shown, int(tabs_shown * RNG.uniform(0.2, 0.45)),
                    composer, chat, agent, RNG.randint(0, 6) if active else 0,
                    composer + chat + agent, 0, 0, 0, model,
                    ".ts" if active else "", ".py" if active else "", "9.9.0-demo",
                ])
                if active:
                    for _ in range(RNG.randint(3, 8)):
                        model = RNG.choice(CURSOR_MODELS)
                        t = tokens(scale / 4)
                        usage = {
                            "inputTokens": t[0], "outputTokens": t[1],
                            "cacheReadTokens": t[2], "cacheWriteTokens": t[3],
                            "totalCents": cents(CURSOR_RATES[model], t),
                        }
                        cursor_events.append([
                            epoch_ms(day, RNG.randint(8, 19), RNG.randint(0, 59)),
                            email, model, "Included in Business",
                            str(model == "cursor-max-demo").lower(), 1.0, "true",
                            json.dumps(usage, separators=(",", ":")), "false",
                        ])

        if not weekend:
            t = tokens(0.5)
            claude_rows.append([
                day.isoformat(), "api_actor", API_KEY, ORG_ID, "api", "non-interactive",
                RNG.randint(10, 30), 0, 0, 0, 0, *t,
                cents(CLAUDE_RATES["claude-haiku-demo"], t), "claude-haiku-demo",
            ])

    write("claude_code_usage.csv", [
        "date", "actor_type", "actor_id", "organization_id", "customer_type",
        "terminal_type", "num_sessions", "lines_added", "lines_removed",
        "commits_by_claude_code", "pull_requests_by_claude_code",
        "total_input_tokens", "total_output_tokens", "total_cache_read_tokens",
        "total_cache_creation_tokens", "total_estimated_cost_cents", "models_used",
    ], claude_rows)
    write("cursor_daily_usage.csv", [
        "date", "email", "isActive", "totalLinesAdded", "totalLinesDeleted",
        "acceptedLinesAdded", "acceptedLinesDeleted", "totalApplies",
        "totalAccepts", "totalRejects", "totalTabsShown", "totalTabsAccepted",
        "composerRequests", "chatRequests", "agentRequests", "cmdkUsages",
        "subscriptionIncludedReqs", "apiKeyReqs", "usageBasedReqs", "bugbotUsages",
        "mostUsedModel", "applyMostUsedExtension", "tabMostUsedExtension",
        "clientVersion",
    ], cursor_daily)
    write("cursor_usage_events.csv", [
        "timestamp", "userEmail", "model", "kind", "maxMode", "requestsCosts",
        "isTokenBasedCall", "tokenUsage", "isFreeBugbot",
    ], cursor_events)

    print(f"{len(claude_rows)} Claude Code rows, {len(cursor_daily)} Cursor daily rows, "
          f"{len(cursor_events)} Cursor events")


if __name__ == "__main__":
    main()
