#!/usr/bin/env python3
"""Turn data/raw/ into cards — templates only, no model, no cost.

Also prunes expired signal cards. Writes data/cards.new.json for review;
merge into cards.json with --merge once you're happy.

Run: python3 scripts/make_cards.py [--merge]
"""
import argparse
import json
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
CARDS = ROOT / "data" / "cards.json"
NEW = ROOT / "data" / "cards.new.json"

TODAY = date.today().isoformat()
HEADLINE_TTL_DAYS = 7
DATA_TTL_DAYS = 30


def load(name):
    p = RAW / name
    if not p.exists():
        return []
    return json.loads(p.read_text(encoding="utf-8")).get("rows", [])


def card(cid, group, kind, tag, hook, detail, source, url, confidence="verified"):
    return {
        "id": cid, "group": group, "kind": kind, "tag": tag,
        "hook": hook, "detail": detail, "source": source,
        "sourceUrl": url, "confidence": confidence, "added": TODAY,
    }


def from_gie():
    rows = load("gie_storage.json")
    if not rows:
        return []
    latest = rows[0]
    pct = latest.get("full_pct")
    if pct is None:
        return []
    pct = float(pct)
    if pct >= 90:
        read = "comfortably ahead of the heating season."
    elif pct >= 75:
        read = "on track, but with less cushion than a comfortable year."
    else:
        read = "thin for this point in the year — worth watching."
    return [card(
        f"s-gie-{TODAY}", "macro", "signal", "Live data",
        f"EU gas storage is {pct:.0f}% full.",
        f"That is {read} Storage is the buffer between a cold snap and a price spike, which is why the fill level is watched so closely into winter.",
        "GIE AGSI+", "https://agsi.gie.eu",
    )]


def from_fred():
    out = []
    labels = {
        "T10Y2Y": ("The 10-year/2-year spread is at {v}.",
                   "A negative spread means short-term debt pays more than long-term — historically a recession signal, though the lag has been long and variable."),
        "DGS10": ("The US 10-year Treasury yields {v}%.",
                  "The 10-year is the reference rate much of global finance prices off, from mortgages to equity valuations."),
    }
    for row in load("fred.json"):
        sid = row["series"]
        if sid not in labels:
            continue
        val = row["latest"]["value"]
        hook, detail = labels[sid]
        out.append(card(
            f"s-fred-{sid}-{TODAY}", "macro", "signal", "Live data",
            hook.format(v=val), detail, "FRED",
            f"https://fred.stlouisfed.org/series/{sid}",
        ))
    return out


def from_headlines():
    """Headline pointers. Body text is never stored or shown — see CLAUDE.md."""
    out = []
    for i, row in enumerate(load("ft_headlines.json")[:3]):
        out.append(card(
            f"s-ft-{TODAY}-{i}", "macro", "signal", "Worth a read",
            row["headline"],
            "Open it in your own subscription — this card is a pointer, not a summary.",
            row.get("source", "FT"), row.get("link", ""),
        ))
    return out


def from_wikipedia():
    out = []
    for i, row in enumerate(load("wikipedia.json")[:3]):
        if not row.get("text"):
            continue
        out.append(card(
            f"s-wiki-{TODAY}-{i}", "general", "signal", "On this day",
            f"{row['year']}: {row['text'][:90]}",
            row["text"],
            "Wikipedia", row.get("url") or "https://en.wikipedia.org",
            confidence="unverified",
        ))
    return out


def expired(c):
    if c.get("kind") != "signal" or not c.get("added"):
        return False
    ttl = HEADLINE_TTL_DAYS if c.get("source", "") in {"FT", "Reuters", "Bloomberg"} else DATA_TTL_DAYS
    added = datetime.fromisoformat(c["added"]).date()
    return date.today() - added > timedelta(days=ttl)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--merge", action="store_true", help="merge into cards.json and prune expired")
    args = ap.parse_args()

    fresh = from_gie() + from_fred() + from_headlines() + from_wikipedia()
    NEW.write_text(json.dumps(fresh, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"generated {len(fresh)} cards → data/cards.new.json")

    if not args.merge:
        print("review it, then re-run with --merge")
        return

    existing = json.loads(CARDS.read_text(encoding="utf-8"))
    kept = [c for c in existing if not expired(c)]
    pruned = len(existing) - len(kept)

    by_id = {c["id"]: c for c in kept}
    for c in fresh:
        by_id[c["id"]] = c

    merged = sorted(by_id.values(), key=lambda c: c["id"])
    CARDS.write_text(json.dumps(merged, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"merged. {pruned} expired pruned, {len(merged)} cards total")
    print("now run: python3 scripts/validate_cards.py")


if __name__ == "__main__":
    main()
