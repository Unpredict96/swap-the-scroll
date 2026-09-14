#!/usr/bin/env python3
"""Pull from open sources into data/raw/. Stdlib + requests only.

Every fetcher is a small function returning a list of dicts. They are
deliberately independent so one failing source never blocks the rest.

API keys come from a .env file (see .env.example) and are never committed.

Run: python3 scripts/fetch_sources.py [--only fred,gie]
"""
import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path
from xml.etree import ElementTree

try:
    import requests
except ImportError:
    sys.exit("pip install requests")

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)
TIMEOUT = 20
UA = {"User-Agent": "swap-the-scroll/1.0 (personal learning app)"}


def load_env():
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


# --------------------------------------------------------------------------
# Fetchers. Each returns a list of dicts; make_cards.py turns them into cards.
# --------------------------------------------------------------------------

def fetch_gie_storage():
    """EU gas storage levels. Free key: register at https://agsi.gie.eu"""
    key = os.environ.get("GIE_API_KEY")
    if not key:
        print("  skip gie: no GIE_API_KEY in .env")
        return []
    r = requests.get("https://agsi.gie.eu/api",
                     params={"country": "EU"},
                     headers={**UA, "x-key": key}, timeout=TIMEOUT)
    r.raise_for_status()
    data = r.json().get("data", [])
    return [{
        "date": d.get("gasDayStart"),
        "full_pct": d.get("full"),
        "trend": d.get("trend"),
        "country": "EU",
    } for d in data[:14]]


def fetch_fred(series_ids=("T10Y2Y", "CPIAUCSL", "DGS10")):
    """US macro series. Free key: https://fred.stlouisfed.org/docs/api/api_key.html"""
    key = os.environ.get("FRED_API_KEY")
    if not key:
        print("  skip fred: no FRED_API_KEY in .env")
        return []
    out = []
    for sid in series_ids:
        r = requests.get("https://api.stlouisfed.org/fred/series/observations",
                         params={"series_id": sid, "api_key": key,
                                 "file_type": "json", "sort_order": "desc", "limit": 5},
                         headers=UA, timeout=TIMEOUT)
        r.raise_for_status()
        obs = r.json().get("observations", [])
        if obs:
            out.append({"series": sid, "latest": obs[0], "previous": obs[1] if len(obs) > 1 else None})
    return out


def fetch_rss_headlines(url, source_name, limit=10):
    """Headlines ONLY from a public RSS feed.

    Deliberately stores title, standfirst, link and date and nothing else.
    Do not extend this to fetch article bodies — see CLAUDE.md attribution
    rules. For paywalled titles the card is a pointer, not a substitute.
    """
    r = requests.get(url, headers=UA, timeout=TIMEOUT)
    r.raise_for_status()
    root = ElementTree.fromstring(r.content)
    items = []
    for item in root.iter("item"):
        def text(tag):
            el = item.find(tag)
            return el.text.strip() if el is not None and el.text else ""
        desc = text("description")
        items.append({
            "source": source_name,
            "headline": text("title"),
            "standfirst": desc[:300],
            "link": text("link"),
            "published": text("pubDate"),
        })
        if len(items) >= limit:
            break
    return items


def fetch_ft():
    return fetch_rss_headlines("https://www.ft.com/rss/home", "FT")


def fetch_wikipedia_featured():
    """Wikipedia 'on this day' / featured. Always marked unverified downstream."""
    today = date.today()
    url = f"https://api.wikimedia.org/feed/v1/wikipedia/en/featured/{today:%Y/%m/%d}"
    r = requests.get(url, headers=UA, timeout=TIMEOUT)
    r.raise_for_status()
    data = r.json()
    out = []
    for ev in data.get("onthisday", [])[:8]:
        pages = ev.get("pages") or []
        out.append({
            "year": ev.get("year"),
            "text": ev.get("text"),
            "url": pages[0].get("content_urls", {}).get("desktop", {}).get("page") if pages else None,
        })
    return out


FETCHERS = {
    "gie": ("gie_storage.json", fetch_gie_storage),
    "fred": ("fred.json", fetch_fred),
    "ft": ("ft_headlines.json", fetch_ft),
    "wikipedia": ("wikipedia.json", fetch_wikipedia_featured),
}


def main():
    load_env()
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="comma-separated subset, e.g. fred,gie")
    args = ap.parse_args()

    wanted = set(args.only.split(",")) if args.only else set(FETCHERS)

    for name, (filename, fn) in FETCHERS.items():
        if name not in wanted:
            continue
        print(f"fetching {name}…")
        try:
            rows = fn()
            if rows:
                (RAW / filename).write_text(
                    json.dumps({"fetched": date.today().isoformat(), "rows": rows},
                               indent=1, ensure_ascii=False), encoding="utf-8")
                print(f"  wrote {len(rows)} rows to data/raw/{filename}")
        except Exception as e:
            print(f"  failed: {e}")


if __name__ == "__main__":
    main()
