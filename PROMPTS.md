# Vibe coding log

Every prompt sent to the AI coding assistant, in order. Fill this in **as you go** —
it cannot be reconstructed afterwards, and it's the part the project is actually
graded on.

**Assistant used:** Claude Code (CLI)
**Model:** claude-sonnet-5
**Total session time:** ~45 min for app.py build, plus a later session for
dataset expansion (5→39 rows) and a visual redesign pass (Aug 14 2026)

---

## Template — copy this block for each prompt

### Prompt N — <what you were trying to get>

**Prompt sent**

```
<paste the exact text>
```

**What came back**

<one or two lines: what it generated>

**Did it work?**

<Worked as-is / Partially / Failed>

**What I had to fix**

<the specific thing that was wrong — wrong column name, hallucinated library,
chart that didn't render, date parsing broken, etc.>

**Follow-up prompt, if any**

```
<paste it>
```

**Screenshot:** `screenshots/prompt-N.png`

---

## Prompt 1 — Scaffold the app and load the CSV

**Prompt sent**

```
I have a CSV at data/shows.csv with columns: show_title, company, language,
genre, venue, city, region, date, start_time, price_min, price_max,
ticketing_platform, source_url, collected_on, notes.

Build a Streamlit app in app.py that loads this CSV with pandas, parses `date`
as a datetime, derives a `day_of_week` and `month` column, and displays the raw
dataframe with a title and a row count. Nothing else yet.
```

**What came back**

A working `app.py`: cached `load_data()` loading `data/shows.csv`, `date` parsed
with `pd.to_datetime(errors="coerce")`, `day_of_week`/`month` derived from it, a
title, a row-count line, and `st.dataframe(df)`.

**Did it work?**

Worked as-is. Checked date parsing separately against the real CSV
(`pd.to_datetime` on the 5 rows) before trusting it — 0 unparseable dates.

**What I had to fix**

Nothing at this stage. The dependencies (`streamlit`, `pandas`, `plotly`,
`anthropic`, `python-dotenv`) weren't installed yet, so I created a `.venv` and
installed `requirements.txt` before this would even run.

**Screenshot:** `screenshots/prompt-1-raw-table.png`

---

## Prompt 2 — Sidebar filters

**Prompt sent**

```
Add sidebar filters for language, genre, region, and company (multiselect,
defaulting to all values) and a date range picker. Filter the dataframe by all
of them combined. Show a count of "N of M shows match" above four KPI metrics:
total shows, companies, venues, languages.
```

**What came back**

A `multiselect_filter()` helper reused for all four categorical filters, a
`st.sidebar.date_input` range picker, a combined boolean mask, and
`st.columns(4)` with `st.metric` for the KPIs.

**Did it work?**

Partially. It ran without errors, but it was silently wrong: any row with a
blank value in a filtered column (the CSV has one row with no `language`
confirmed yet — a season announcement placeholder) never matched `isin()`
against the list of non-null unique values, even with every option selected.
That row disappeared from the app permanently with no error to signal it.

**What I had to fix**

Added `df[col] = df[col].fillna("Unknown")` for the four filter columns before
building the filter options, so blank values become an explicit, selectable
"Unknown" bucket instead of vanishing. Verified the fix by checking the KPI
line went from "5 of 5... but only showing 4 rows worth of variety" to
correctly reflecting all 5 rows with "Unknown" appearing as a language option.

**Screenshot:** `screenshots/prompt-2-filters.png`

---

## Prompt 3 — First charts

**Prompt sent**

```
Add two tabs: "Price distribution" (box plot of price by language, colored by
genre, using the midpoint of price_min/price_max) and "Venue concentration"
(horizontal bar chart of show count per venue). Handle rows with no price
gracefully — don't drop them silently, tell the user how many were excluded.
```

**What came back**

`st.tabs()` with a price box plot (`px.box`, `points="all"`) and a venue bar
chart (`px.bar`, horizontal, sorted ascending).

**Did it work?**

Worked as-is on the first pass. Only 2 of 5 rows have both `price_min` and
`price_max` filled in, so the "3 shows have no listed price and are excluded"
caption is the more informative part of that tab right now — a good sign the
excluded-count message was worth asking for explicitly.

**What I had to fix**

Nothing functionally, but `st.plotly_chart(..., use_container_width=True)`
logged a Streamlit deprecation warning in the server log (removed after
2025-12-31, replaced by `width="stretch"`). Fixed across all five chart calls
in the file with a single `sed` pass rather than waiting for it to break.

**Screenshot:** `screenshots/prompt-3-charts.png`

---

## Prompt 4 — Weekend saturation analysis

**Prompt sent**

```
Add three more tabs. "Weekend saturation": bar chart of shows per date, bars
with 2+ shows highlighted in a different color, plus a list below naming which
shows collide on each such date. "Seasonality": bar chart of show count by
calendar month, in Jan-Dec order, with a caption noting the Aug-Nov desi
festival season to watch for as the dataset grows. "Company activity": bar
chart of shows per company, plus a table of first/last show date per company
sorted so the longest-quiet companies surface first.
```

**What came back**

Three tabs matching the spec, using `groupby` on `date.dt.date` for collisions,
`value_counts().reindex(MONTH_ORDER)` for the month order, and a
`groupby("company").agg(...)` for activity.

**Did it work?**

Worked as-is. With only 5 rows on 5 distinct dates there are no real collisions
to show yet — expected, and a direct symptom of the dataset being far short of
the 60-100 row target in `COLLECTION_GUIDE.md` (see Learnings).

**What I had to fix**

Nothing broke, but I intentionally kept the month order pinned to the calendar
(`MONTH_ORDER` list) instead of `value_counts()`'s default frequency order —
otherwise a sparse dataset would produce a seasonality chart with months in a
meaningless order.

**Screenshot:** `screenshots/prompt-4-saturation.png`

---

## Prompt 5 — AI extraction panel

**Prompt sent**

```
Add an "AI extract" tab: a text area for a raw show announcement and a button
that sends it to Claude, asking it to return JSON matching the CSV schema
columns, with strict instructions to use null instead of guessing any field
not explicitly in the text. Display the result with st.json. Handle a missing
ANTHROPIC_API_KEY and a non-JSON response without crashing the app.
```

**What came back**

An `extract_show()` function calling `anthropic.Anthropic().messages.create()`
with `model="claude-sonnet-5"`, a prompt enumerating the schema and enum rules,
markdown-fence stripping on the response, and a tab wiring it to a button with
`st.error`/`st.warning`/`st.spinner` states.

**Did it work?**

Worked as-is for the error-handling paths, which is what I could verify without
spending a real API key: tested with no `ANTHROPIC_API_KEY` set and got the
intended graceful red error box instead of a stack trace. Haven't yet run it
against a live key with a real announcement — that's the one thing in this app
still unverified end-to-end.

**What I had to fix**

Nothing yet — but this is the one panel I'd stress-test harder before the demo
video, specifically the markdown-fence-stripping logic (`text.strip("`")`),
since a model response that doesn't wrap JSON in fences at all would currently
pass through untouched, which is fine, but one that opens with something other
than a fence or a `{` would break `json.loads` and only be caught by the
generic `except Exception` — acceptable for a v1, not something I'd leave
unguarded in a production tool.

**Screenshot:** `screenshots/prompt-5-ai-extract.png`

---

## Prompt 6 — Visual redesign

**Prompt sent**

```
The UI looks like stock Streamlit — flat black background, no visual
hierarchy, default plotly colors. Redesign it: dark theme via
.streamlit/config.toml, card-styled KPI metrics, a fixed categorical color
palette applied consistently across every chart (not plotly's default
per-chart auto-assignment), tab icons, and a themed plotly template (shared
surface/gridline/ink colors) applied to every figure.
```

**What came back**

A `.streamlit/config.toml` dark theme, a `CUSTOM_CSS` block styling
`stMetric` into bordered cards, a `themed()` helper applying shared
surface/gridline/ink colors to every plotly figure, a fixed `GENRE_COLORS`
dict (five colors from a pre-validated colorblind-safe categorical order,
not plotly's auto-cycling), and emoji icons on each tab label.

**Did it work?**

Partially. The theme and cards worked first pass. But the first version of
`themed()` set `title_font` on every figure even though no chart sets an
actual title — Plotly rendered the literal string "undefined" as a chart
title on every single tab. Not visible without actually loading the app;
would have shipped in the demo video if I'd only read the diff.

**What I had to fix**

Dropped the unused `title_font` line from `themed()`. Separately — while
eyeballing the venue chart with the new styling — noticed "Cubberley
Theater" vs "Cubberley Theatre" and "Douglas Morrisson Theatre" vs "The
Douglas Morrisson Theatre" were rendering as separate bars for the same
real venue (venues went from 29 "unique" down to 24 once standardized).
This was a spelling-consistency bug in my own data-collection pass from
earlier, exactly the failure mode `COLLECTION_GUIDE.md` warns about for
company names — the redesign is what made it visible, since a cleaner
chart made the duplicate bars obvious instead of blending into visual
noise. Also hit a stale-cache issue: `st.cache_data` doesn't know the CSV
changed on disk, so the venue count didn't update until I restarted the
server, not just reran the script.

**Screenshot:** `screenshots/prompt-6-redesign.png`

---

## Learnings

- **Where the assistant was strongest:** Generating correct, idiomatic
  pandas/plotly/streamlit in one pass for well-specified chart requests — the
  charts in prompts 3 and 4 needed zero fixes. Being explicit about edge cases
  in the prompt itself (empty selection, no price, missing key) meant those
  cases were handled up front instead of discovered later.
- **Where it consistently got things wrong:** Anything involving `NaN`/blank
  values needed a second pass. The `isin()` filter bug in Prompt 2 is the
  clearest example — it's the kind of bug that doesn't error, it just quietly
  deletes a row from every view, which is worse than a crash for a data app.
- **The single prompt that saved the most time:** Prompt 4, because it bundled
  three related tabs into one spec instead of three round trips — the shared
  `filtered` dataframe and tab structure meant the assistant didn't have to be
  reminded of conventions already established in prompts 1-3.
- **What I'd do differently next time:** Ask for the `fillna("Unknown")`
  pattern explicitly in Prompt 2 instead of catching it after the fact — I now
  know blank categorical values are a near-certainty in hand-collected data,
  so I'd bake the fix into the first prompt rather than the review pass.
- **What I still had to write or fix by hand:** The `sed` cleanup for the
  `use_container_width` deprecation, and standing up the local run
  environment itself (`.venv`, `pip install -r requirements.txt`,
  `.claude/launch.json` for the dev-server preview) — none of that is
  "coding," but all of it gated whether any of the above could be verified
  rather than just trusted.
- **Dataset expansion (post-initial-build):** Went from 5 to 39 rows by
  working the guide's own source list — Sulekha (Marathi/Hindi/Gujarati/
  Tamil/Telugu/Bengali/Punjabi pages plus the general Bay Area listing),
  Naatak's full Season 31, Eventbrite, India Currents, and 13 English-language
  comparison shows across 9 mainstream Bay Area theater companies. Used
  parallel research agents to cover the sources faster, but did the filtering
  and merge myself — several titles that looked like theater on first pass
  turned out not to be ("YAHOO! A Shankar Jaikishan Musical" is a tribute
  concert despite "Musical" in the name; "Thank You 5 (Uff Yeh Gehraiyaan)"
  is a yacht party; "Rajkumari" is poetry/storytelling, not a scripted play)
  and were excluded rather than counted toward the row total. Every row has a
  real source URL; every unconfirmed or multi-date-range show is flagged
  `PLACEHOLDER` in notes per the guide's own convention. Still short of the
  60-100 target — 39 is a defensible middle ground given the deadline, and
  the app now surfaces a genuine same-day collision (2026-06-05) that
  wasn't visible in the original 5-row sample.
- **A second real bug this surfaced:** hand-editing one CSV row directly
  (updating the old Naatak placeholder to a confirmed show) broke `pd.read_csv`
  with "Expected 15 fields, saw 16" — an unquoted comma in a notes field I
  typed by hand, invisible until parsed. Every other new row went through
  `csv.DictWriter`, which quotes automatically; this one didn't because I
  edited it directly. Fixed by replacing the comma with a semicolon. Lesson:
  script-generate CSV rows even for "just one row," not just bulk edits.
