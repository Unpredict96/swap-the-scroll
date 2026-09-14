# Swap the scroll

A finite daily feed of macro, energy-market and general-knowledge cards —
built to replace doomscrolling rather than relocate it.

Plain HTML/CSS/JS. No build step, no dependencies, no recurring cost.

## Run it

```bash
python3 -m http.server 8000
```

Then open <http://localhost:8000>. A server is required — ES modules and
the service worker don't work from `file://`.

In VS Code, the Live Server extension does the same thing with one click.

## Install it on your phone

1. Deploy to any static host with HTTPS (GitHub Pages, Netlify, Cloudflare
   Pages — all free tiers).
2. Open the URL on your phone.
3. iOS: Share → Add to Home Screen. Android: menu → Install app.

It then opens full-screen with no browser chrome, and works offline.

## Add cards

Cards live in `data/cards.json` — content, not code. Three ways to add:

**By hand.** Edit the JSON, then:
```bash
python3 scripts/validate_cards.py
```

**From live data (free, automatic).**
```bash
cp .env.example .env       # add your free API keys
python3 scripts/fetch_sources.py
python3 scripts/make_cards.py          # writes cards.new.json for review
python3 scripts/make_cards.py --merge  # merges and prunes expired
```

**With Claude Code (free, best writing).**
Open `scripts/generate_prompt.md` and hand the prompt to Claude Code. It
writes a batch to `cards.new.json` for you to review before merging.

## Source rules

`data/sources.json` is the registry. Two rules matter:

- **Argus, ICIS, Kpler and S&P Global are blocked.** Seat-licensed
  platforms; piping their content into an app breaches the terms. The
  validator fails the build if a card cites them.
- **Paywalled press is headline-only.** FT and Reuters cards carry the
  headline and a link, nothing more. You open it in your own subscription.

Wikipedia-derived cards are always marked unverified and say so on the card
face — the licence requires attribution, and the accuracy varies.

## Layout

```
index.html              app shell
src/app.js              feed logic, daily cap, streak
src/storage.js          localStorage wrapper
src/app.css             styles
data/cards.json         the deck
data/sources.json       source registry + licence rules
scripts/                fetch, template, validate
CLAUDE.md               project brief for Claude Code
```

## Design intent

The daily cap and the streak are the point. A feed that never ends is the
problem being solved, so anything that makes this one more endless is a
regression. See `CLAUDE.md` before changing that behaviour.
