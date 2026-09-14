# Swap the Scroll — project brief

## What this is

A personal, installable web app that replaces doomscrolling on TikTok/Instagram
with a swipeable feed of macro-economics, energy-market and general-knowledge
cards. Built for one user (Jackie — European gas & LNG markets, London).

It is deliberately **not** infinite. A daily cap and a streak are the core of the
design: the app is meant to end, every day, at a natural stopping point. Any
change that makes the feed more endless is a regression, not a feature.

## Non-negotiable design constraints

1. **The daily cap stays.** Default 10 cards/day. The "keep browsing anyway"
   escape hatch is intentional (autonomy, not a trap) but must remain a
   deliberate second action, never the default path.
2. **No engagement mechanics beyond the streak.** No notifications begging for
   return visits, no variable-reward animations, no "you're missing out" copy.
3. **Every card is attributed.** `source` and `confidence` are required fields.
   Cards render their provenance on the face. See "Attribution rules" below.
4. **Offline first.** The feed must work with no network — commute use case.
5. **Zero recurring cost.** No paid APIs. See "Content pipeline" below.

## Stack

Plain HTML/CSS/JS. No framework, no build step, no dependencies. This is
deliberate: the app is small, the user is more fluent in Python than JS, and a
build step is a maintenance tax with no payoff at this size.

Python 3 for the ingestion scripts (stdlib + `requests` only).

Do not introduce React, a bundler, or a package manager without asking first.

## Layout

```
index.html          markup + app shell
src/app.js          feed logic, rendering, daily cap, streak
src/storage.js      localStorage wrapper (was window.storage in the prototype)
src/app.css         styles
manifest.webmanifest  PWA manifest
sw.js               service worker — offline cache
data/cards.json     the card deck (content, not code)
data/sources.json   source registry: endpoints, licences, attribution rules
scripts/fetch_sources.py    pulls from open APIs → data/raw/
scripts/make_cards.py       templates raw data → card JSON (no LLM)
scripts/validate_cards.py   schema + attribution check, run before commit
scripts/generate_prompt.md  the prompt to hand Claude Code for batch writing
```

## Card schema

```json
{
  "id": "m11",
  "group": "macro" | "general",
  "kind": "fact" | "quiz" | "signal",
  "tag": "Macro & energy",
  "hook": "Short, memorable, <=100 chars. The thing you'd remember.",
  "detail": "Why it matters. 1-3 sentences. Plain language.",
  "source": "FRED",
  "sourceUrl": "https://...",
  "confidence": "verified" | "unverified",
  "added": "2026-09-14"
}
```

- `kind: "signal"` is for live-data cards (storage levels, rate decisions) and
  for FT/Reuters headline pointers. Signal cards expire — see below.
- `confidence: "unverified"` renders a visible marker on the card face. Use it
  for anything Wikipedia-derived or otherwise not from a primary source.

## Attribution rules

- **Primary data sources** (FRED, ECB, EIA, GIE, ENTSOG, ONS, Eurostat):
  `confidence: "verified"`. Name the source on the card.
- **Wikipedia / Wikidata**: always `confidence: "unverified"`. The card face
  must show "Wikipedia — verify before citing". Content is CC BY-SA, so
  attribution is a licence requirement, not just good manners.
- **FT, Reuters, Bloomberg and other paywalled press**: headline + standfirst +
  link ONLY, pulled from their public RSS feeds. Never fetch, store, cache or
  reproduce article body text. The card exists to say "this looks relevant",
  and the user opens it in their own subscription. This boundary is not
  negotiable — do not add full-text scraping, archive-site fallbacks, or
  paywall bypass of any kind, even if asked.
- **Never ingest Argus, ICIS, Kpler or S&P Global.** These are seat-licensed
  professional platforms. Piping their content into an app breaches the terms,
  even for personal use. No exceptions.

## Content pipeline — zero cost by design

Three tiers, in order of preference:

**Tier 1 — templates (no model, fully automatic).**
`scripts/fetch_sources.py` pulls open APIs into `data/raw/`.
`scripts/make_cards.py` fills templates with that data. Deterministic, free,
runs on a cron. Good for storage levels, CPI prints, rate decisions.

**Tier 2 — Claude Code batch writing (no marginal cost).**
When the deck needs fresh non-data cards, run Claude Code against
`scripts/generate_prompt.md` with recent raw data in context. It writes a batch
of cards to `data/cards.new.json` for the user to review, then merge. This is
the main path for good writing. Review before merge is required, not optional.

**Tier 3 — local model (optional, unattended).**
If fully automated generation is ever wanted, wire in Ollama with a small local
model. Documented as an option; not built. Do not add a paid API in its place.

## Signal card expiry

Cards with `kind: "signal"` carry an `added` date and expire after 7 days
(headlines) or 30 days (data snapshots). `make_cards.py` prunes expired signal
cards on each run. Fact and quiz cards never expire.

## Backlog — roughly prioritised

1. Icons: `icons/` currently holds a generated placeholder set. Replace with
   something the user actually likes.
2. Wire `fetch_sources.py` to real endpoints. FRED and GIE AGSI+ need free API
   keys — read from `.env`, never commit them. `.env.example` is the template.
3. Deploy. Static hosting is enough (GitHub Pages, Netlify, Cloudflare Pages).
   Needs HTTPS for the service worker to register.
4. "Saved cards" review screen — currently cards can be saved but not browsed.
   Spaced repetition on saved cards is the obvious extension.
5. Weekly digest: roll the week's saved cards into a summary.
6. Hook into the user's existing IEA/ACER/Bruegel publication watcher script
   rather than duplicating that logic here.

## Conventions

- British English in all user-facing copy.
- Sentence case. No title case, no ALL CAPS.
- No emoji in the UI.
- Keep `data/cards.json` sorted by id. One card per line is fine — readability
  over pretty-printing.
- Run `python3 scripts/validate_cards.py` before committing card changes.
