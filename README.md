# Rangmanch

A consumer-facing calendar for the Bay Area community theater and desi standup
scene — every upcoming play, musical and comedy night in one place, built from
a hand-collected dataset.

**Live:**
[Rangmanch calendar](https://omkarsali-hub.github.io/bay-area-stage-analytics/) ·
[Analytics dashboard](https://omkarsali-hub-bay-area-stage-analytics-app-i2f8wp.streamlit.app/)

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

**[`index.html`](index.html) — Rangmanch, the primary deliverable.**
Live at **[omkarsali-hub.github.io/bay-area-stage-analytics](https://omkarsali-hub.github.io/bay-area-stage-analytics/)**.
A public calendar: pick a night, see what's on, click through to buy. Only
shows on or after today are listed — this is a "what can I go see" tool, not
an archive.

**[`app.py`](app.py) — a separate analytics dashboard**, run standalone (not
embedded in Rangmanch). Live at
**[bay-area-stage-analytics.streamlit.app](https://omkarsali-hub-bay-area-stage-analytics-app-i2f8wp.streamlit.app/)**.
Same dataset, filterable, with:

| View | Question it answers |
|---|---|
| Price distribution | What does a ticket cost by language and genre? |
| Weekend saturation | How many shows collide on the same date? |
| Venue concentration | Which venues carry the scene? |
| Seasonality | How do shows cluster around festivals? |
| Company activity | Who produces most, and who went quiet? |
| AI extract panel | Paste a raw announcement → Claude returns a structured row |

The analytics app covers the *full* dataset, including past shows — Rangmanch's
calendar deliberately only shows what's still bookable.

## Dataset

`data/shows.csv` — 64 collected listings for Bay Area community theater,
cultural programs and desi standup, plus an English-language comparison set.
Multi-weekend runs are itemized one row per performance date (not just the
opening night) wherever the actual schedule is known. See
`data/COLLECTION_GUIDE.md` for the schema, sources and collection rules, and
`PROMPTS.md` for how the dataset was built out.

Every row carries a `source_url` so any figure in either app can be traced back
to where it came from. Every "Get tickets" link on Rangmanch goes straight to
that same source — Rangmanch never takes payment or holds tickets itself.

## Run locally

Both apps are live (links above) — this is only needed to run your own copy.

```bash
pip install -r requirements.txt

# Rangmanch — serve it, don't just double-click index.html
# (some browsers restrict features on bare file:// pages)
python3 -m http.server 8000
```

Then open **http://localhost:8000/index.html**.

The analytics dashboard is separate:

```bash
streamlit run app.py
```

The AI extraction panel needs an Anthropic API key:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

## Vibe coding log

Every prompt used to build this, in order, with what needed fixing:
see [PROMPTS.md](PROMPTS.md).

## Limitations

- The dataset is a hand-collected sample, not a complete census of the scene.
  If a show you know of is missing, it's a collection gap, not a bug — happy
  to add it given the show name/venue/dates.
- Price ranges are list prices; discounts and comps aren't captured.
- Venue capacity is not yet included, so "saturation" measures show count, not seats.
- A few multi-week runs (flagged `PLACEHOLDER` in `notes`) are still only
  represented by their opening date, where the actual day-of-week performance
  pattern wasn't available or confirmed.
