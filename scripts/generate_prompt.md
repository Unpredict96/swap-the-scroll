# Prompt: write a batch of cards

Hand this to Claude Code when the deck needs fresh non-data cards. This is
Tier 2 in the content pipeline (see CLAUDE.md) — no paid API, just your
existing Claude Code session.

---

## The prompt

> Read `CLAUDE.md`, `data/cards.json` and `data/sources.json`.
>
> Write **12 new cards** for the deck: 7 macro/energy, 5 general knowledge.
> Mix of `fact` and `quiz` kinds. Output to `data/cards.new.json` only —
> do not touch `cards.json`, I will review and merge.
>
> Rules:
> - Don't repeat anything already in `cards.json`. Check first.
> - Every card needs a real `source` and `sourceUrl` I can click through to.
>   If you can't source a claim, don't write the card.
> - Anything Wikipedia-derived gets `confidence: "unverified"`.
> - `hook` under 110 chars — it must be the thing I'd actually remember.
>   Not "X is important", but the specific, surprising, concrete fact.
> - `detail` is 1–3 sentences on why it matters. Plain language. No jargon
>   unless the jargon is the point.
> - Assume I already know the basics of gas and LNG markets. Aim at the
>   level of something I'd half-know and want sharpened, not an explainer
>   for a beginner.
> - Quiz cards: `hook` is the question, `detail` is the answer plus one line
>   of context. Questions should be answerable, not obscure.
> - British English. Sentence case. No emoji.
>
> When done, run `python3 scripts/validate_cards.py` against the merged
> result and fix anything it flags.

---

## Topics worth mining

**Macro/energy** — storage economics and summer/winter spreads; the
JKM–TTF arbitrage; regas capacity vs send-out; interruptible vs firm
capacity; Norwegian field maintenance seasonality; hub liquidity and why
TTF won; carbon pricing under the ETS; power-gas spark spreads; the
difference between proven, probable and possible reserves; how a cargo
diversion actually happens; balancing regimes and imbalance charges;
why weather derivatives exist.

**General** — trade route history; the origins of financial instruments;
food and wine geography and appellation law; UK and European history where
it touches commerce; measurement and standards history; how commodities
became commodities.

## Anti-patterns

Cards that fail:
- "Inflation is when prices rise." Too basic. No surprise.
- "The energy transition is complex." Not a fact.
- "Gas prices rose 12% last Tuesday." Perishable and better as a signal card.
- Anything where the interesting bit is in the detail rather than the hook —
  the hook has to carry it.
