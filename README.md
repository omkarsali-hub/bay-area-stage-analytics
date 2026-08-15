# Rangmanch

A consumer-facing calendar for the Bay Area community theater and desi standup
scene — every upcoming play, musical and comedy night in one place, with a
live analytics dashboard pinned alongside it, both reading from the same
hand-collected dataset.

**The Gen Academy — Mastering Agentic AI Bootcamp, Week 1 (Path B)**

## Problem

Bay Area community theater and desi standup — Marathi, Hindi, Gujarati, Tamil and
English productions — has no shared calendar and no public data. Every company
markets on its own Instagram, prices tickets blind, and picks dates blind. Nobody
can see how many shows land on the same Saturday, what a ticket in a given language
typically costs, or which venues are already booked out. Companies routinely compete
for the same audience on the same night without knowing it, and audiences have no
single place to go looking.

No dataset for this existed, so it was built by hand from company sites and
ticketing pages, then turned into two things built on the same data:

## What's here

**[`index.html`](index.html) — Rangmanch, the primary deliverable.** A public
calendar: pick a night, see what's on, click through to buy. Only shows on or
after today are listed — this is a "what can I go see" tool, not an archive.
A persistent side panel keeps the analytics dashboard visible at all times.

**[`app.py`](app.py) — the analytics engine**, embedded in Rangmanch's side
panel via iframe, and also runnable standalone. Same dataset, filterable, with:

| View | Question it answers |
|---|---|
| Price distribution | What does a ticket cost by language and genre? |
| Weekend saturation | How many shows collide on the same date? |
| Venue concentration | Which venues carry the scene? |
| Seasonality | How do shows cluster around festivals? |
| Company activity | Who produces most, and who went quiet? |
| AI extract panel | Paste a raw announcement → Claude returns a structured row |

The analytics panel covers the *full* dataset, including past shows — Rangmanch's
calendar deliberately only shows what's still bookable.

## Dataset

`data/shows.csv` — 39 collected listings for Bay Area community theater,
cultural programs and desi standup, plus an English-language comparison set.
See `data/COLLECTION_GUIDE.md` for the schema, sources and collection rules,
and `PROMPTS.md` for how the dataset was built out.

Every row carries a `source_url` so any figure in either app can be traced back
to where it came from. Every "Get tickets" link on Rangmanch goes straight to
that same source — Rangmanch never takes payment or holds tickets itself.

## Run locally

Rangmanch's side panel needs the analytics app running as a live server, so two
things need to be up at once:

```bash
pip install -r requirements.txt

# terminal 1 — the analytics backend Rangmanch embeds
streamlit run app.py

# terminal 2 — serve Rangmanch itself (don't just double-click index.html;
# opening it as a bare file:// page blocks the iframe in most browsers)
python3 -m http.server 8000
```

Then open **http://localhost:8000/index.html**.

To use `app.py` on its own, without Rangmanch, just open the Streamlit URL it
prints (typically http://localhost:8501).

The AI extraction panel needs an Anthropic API key:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

## Vibe coding log

Every prompt used to build this, in order, with what needed fixing:
see [PROMPTS.md](PROMPTS.md).

## Limitations

- The dataset is a hand-collected sample, not a complete census of the scene.
- Price ranges are list prices; discounts and comps aren't captured.
- Venue capacity is not yet included, so "saturation" measures show count, not seats.
- Each dataset row is one confirmed performance date. A handful of multi-week
  runs (flagged `PLACEHOLDER` in `notes`) are only represented by their opening
  date, so Rangmanch's calendar won't show every night of those runs.
- Rangmanch's side panel is a live iframe, not a static export — it needs
  `app.py` running locally. There's no deployed/hosted version of either app.
