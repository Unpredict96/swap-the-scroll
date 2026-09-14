#!/usr/bin/env python3
"""Validate data/cards.json before it goes anywhere near the app.

Checks schema, duplicate ids, attribution rules and length limits.
Run: python3 scripts/validate_cards.py
Exit code 1 on any error, so it works as a pre-commit hook.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CARDS = ROOT / "data" / "cards.json"
SOURCES = ROOT / "data" / "sources.json"

REQUIRED = {"id", "group", "kind", "hook", "detail", "source", "confidence"}
GROUPS = {"macro", "general"}
KINDS = {"fact", "quiz", "signal"}
CONFIDENCE = {"verified", "unverified"}
MAX_HOOK = 110
MAX_DETAIL = 400

# Sources that must always be marked unverified.
ALWAYS_UNVERIFIED = {"wikipedia", "wikidata", "open trivia db"}


def main() -> int:
    errors, warnings = [], []

    cards = json.loads(CARDS.read_text(encoding="utf-8"))
    if isinstance(cards, dict):
        cards = cards.get("cards", [])

    blocked = set()
    if SOURCES.exists():
        reg = json.loads(SOURCES.read_text(encoding="utf-8"))
        blocked = {s["name"].lower() for s in reg["sources"] if not s.get("usable", True)}

    seen = set()
    for i, c in enumerate(cards):
        where = f"card[{i}] id={c.get('id', '?')}"

        missing = REQUIRED - c.keys()
        if missing:
            errors.append(f"{where}: missing fields {sorted(missing)}")
            continue

        if c["id"] in seen:
            errors.append(f"{where}: duplicate id")
        seen.add(c["id"])

        if c["group"] not in GROUPS:
            errors.append(f"{where}: bad group {c['group']!r}")
        if c["kind"] not in KINDS:
            errors.append(f"{where}: bad kind {c['kind']!r}")
        if c["confidence"] not in CONFIDENCE:
            errors.append(f"{where}: bad confidence {c['confidence']!r}")

        src = c["source"].strip().lower()
        if src in blocked:
            errors.append(f"{where}: source {c['source']!r} is licence-blocked and must not be ingested")
        if src in ALWAYS_UNVERIFIED and c["confidence"] != "unverified":
            errors.append(f"{where}: {c['source']} cards must be confidence='unverified'")

        if len(c["hook"]) > MAX_HOOK:
            warnings.append(f"{where}: hook is {len(c['hook'])} chars (max {MAX_HOOK}) — it will wrap badly")
        if len(c["detail"]) > MAX_DETAIL:
            warnings.append(f"{where}: detail is {len(c['detail'])} chars (max {MAX_DETAIL})")

        if c["kind"] == "signal" and not c.get("added"):
            errors.append(f"{where}: signal cards need an 'added' date so they can expire")
        if not c.get("sourceUrl"):
            warnings.append(f"{where}: no sourceUrl — the reader can't check it")

    for w in warnings:
        print(f"warning: {w}")
    for e in errors:
        print(f"ERROR:   {e}")

    print(f"\n{len(cards)} cards, {len(errors)} errors, {len(warnings)} warnings")
    by_group = {}
    for c in cards:
        by_group[c.get("group", "?")] = by_group.get(c.get("group", "?"), 0) + 1
    print("by group:", by_group)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
