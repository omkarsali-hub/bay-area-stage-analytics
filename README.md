# Bay Area Stage Analytics

A Streamlit app that analyzes the Bay Area community theater and local standup
comedy scene using a dataset built by hand, to find where the market is
oversaturated and where the gaps are.

**The Gen Academy — Mastering Agentic AI Bootcamp, Week 1 (Path B)**

## Problem

Bay Area community theater and desi standup — Marathi, Hindi, Gujarati, Tamil and
English productions — has no shared calendar and no public data. Every company
markets on its own Instagram, prices tickets blind, and picks dates blind. Nobody
can see how many shows land on the same Saturday, what a ticket in a given language
typically costs, or which venues are already booked out. Companies routinely compete
for the same audience on the same night without knowing it.

No dataset for this exists, so I built one by collecting show listings from company
websites and ticketing pages, then built a Streamlit app to analyze it.

## What the app shows

| View | Question it answers |
|---|---|
| Price distribution | What does a ticket cost by language and genre? |
| Weekend saturation | How many shows collide on the same date? |
| Venue concentration | Which venues carry the scene? |
| Seasonality | How do shows cluster around festivals? |
| Company activity | Who produces most, and who went quiet? |
| AI extract panel | Paste a raw announcement → Claude returns a structured row |

## Dataset

`data/shows.csv` — 39 collected listings for Bay Area community theater,
cultural programs and desi standup, plus an English-language comparison set.
See `data/COLLECTION_GUIDE.md` for the schema, sources and collection rules,
and `PROMPTS.md` for how the dataset was built out.

Every row carries a `source_url` so any figure in the app can be traced back to
where it came from.

## Run locally

```bash
pip install -r requirements.txt
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
- Price ranges are list prices; discounts and comps aren't captured.
- Venue capacity is not yet included, so "saturation" measures show count, not seats.
