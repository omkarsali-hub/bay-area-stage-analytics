# Vibe coding log

Every prompt sent to the AI coding assistant, in order. Fill this in **as you go** —
it cannot be reconstructed afterwards, and it's the part the project is actually
graded on.

**Assistant used:** Claude Code (CLI)
**Model:** claude-sonnet-5
**Total session time:** ~45 min for app.py build, plus a later session for
dataset expansion (5→39 rows), a visual redesign pass, and the Rangmanch
integration that became the primary deliverable (all Aug 14 2026)

**Note on screenshots:** taken in one batch at the end of the build (Playwright,
against the running app), not live at each historical step — several early
UI states (e.g. Prompt 1's bare raw table, pre-redesign) no longer exist to
screenshot. Filenames below point to the real feature each prompt introduced,
as it looks in the final app.

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

**Screenshot:** none preserved — the bare raw-table view was fully replaced by
the tabbed layout in Prompt 3 and the redesign in Prompt 6; see those instead.

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

**Screenshot:** `screenshots/analytics-weekend-saturation.png` (sidebar filters visible, expanded)

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

**Screenshot:** `screenshots/analytics-price-distribution.png`, `screenshots/analytics-venue-concentration.png`

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

**Screenshot:** `screenshots/analytics-weekend-saturation.png`, `screenshots/analytics-seasonality.png`, `screenshots/analytics-company-activity.png`

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

**Screenshot:** `screenshots/analytics-ai-extract.png`

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

**Screenshot:** `screenshots/analytics-price-distribution.png` (card-styled metrics, themed chart, tab icons)

---

## Prompt 7 — Rangmanch integration (primary deliverable pivot)

**Context**

I had a separate hand-designed HTML/CSS/JS prototype (`rangmanch-prototype.html`)
— a consumer-facing show calendar with its own carnival/marquee visual identity
and fictional seed data, built independently of this project. I asked to combine
it with the analytics app: Rangmanch as the primary page, the Streamlit analytics
embedded in a persistent side panel, and decided on the specifics (iframe vs.
native rebuild, real data vs. mock, panel layout) through a short back-and-forth
before any code was written.

**Prompt sent**

```
[Attached rangmanch-prototype.html] Can we have one page where we can display
this prototype and have an analytics page somewhere on the side which will
show the analytics? Ask questions, let me make a decision and then execute.
```

Follow-up, after the assistant asked 4 clarifying questions (iframe vs. native
rebuild; real vs. mock data; primary-vs-bonus deliverable; panel behavior):

```
Iframe the Streamlit app. Real data only — no fictional seed shows, upcoming
shows only, relative to Aug 14 2026. This becomes the main submission.
Persistent side column.
```

**What came back**

A Python transform script converting `data/shows.csv` into the prototype's
JS show format, filtered to `date >= 2026-08-14` (21 of 39 rows qualified),
grouped by title+company. A new `index.html` combining the original
Rangmanch design with a two-column sticky layout, the real data wired in,
and a `.streamlit/config.toml` `toolbarMode = "minimal"` tweak plus
`?embed=true` on the iframe URL to hide Streamlit's own chrome.

**Did it work?**

Partially, and in an instructive way. The data transform and calendar/card
logic worked correctly on the first real test — including edge cases I'd
built explicit handling for (null price → "Price TBA" instead of crashing
the tier/sort logic, `$25` instead of `$25–25` when `price_min == price_max`,
a blank `company` falling back to "Producer not listed" rather than showing
`null`). But the analytics iframe itself was blank on the first load.

**What I had to fix**

The browser tool's preview pane loads local `file://` paths outside its
recognized project root as an opaque `data:`-URL snapshot rather than a real
navigation — which silently blocks an iframe to `localhost:8501`
(`net::ERR_BLOCKED_BY_CLIENT`) because a `data:` page has no origin to grant
cross-origin iframe permissions from. Not something visible from reading the
code; only showed up by actually loading the page and checking the network
tab. Fixed by serving `index.html` over a plain local HTTP server
(`python3 -m http.server`) instead of opening it directly — which also
matches how a real user would eventually deploy this, so it's not just a
test workaround. Documented as a required two-terminal step in the README's
"Run locally" section, since forgetting it silently breaks the one thing
that makes this "one page," not two.

**Screenshot:** `screenshots/rangmanch-hero.png`, `screenshots/rangmanch-calendar-and-analytics.png`, `screenshots/rangmanch-cards.png`, `screenshots/rangmanch-mobile.png`

---

## Prompt 8 — Remove the analytics panel; fix missing multi-date shows

**Feedback received**

```
I think we should remove the data analytics part. it looks ugly and doesn't
look nice. also I think some of the data is missing. there are shows
available on the websites but I can't see them on our calendar.
```

**What I did**

Two independent issues, handled separately:

1. **Removed the embedded analytics iframe panel** from `index.html` — deleted
   the two-column layout CSS, the `<aside>` panel, and reverted to a clean
   single-column calendar. `app.py` still exists and still works, just no
   longer embedded; README updated to describe it as a separate tool again.

2. **Investigated the missing-shows report before touching anything.** Traced
   the pipeline end to end: every one of the 21 upcoming rows in
   `data/shows.csv` correctly appeared in `index.html`'s data — no bug. The
   real cause was the known `PLACEHOLDER`-opening-date-only limitation
   (documented back in Prompt 7's dataset section): multi-weekend runs were
   stored as a single row for the first date, so a run playing six weekends
   only ever lit up one square on the calendar.

**What the user reported specifically**

```
Hillbarn theater pickleball shows are running from Aug 20th to Sept 13,
thursday friday saturday sunday. Bombay Talkie 2 turning from Saturday
Sept 12 to Oct 10th friday saturday sunday.. multiple shows on weekends.
```

**What I had to fix**

Re-fetched both source pages before itemizing anything — the day-of-week
pattern the user reported isn't published on either page (they only state a
date range), so I couldn't independently confirm it, but the *end date* is
independently checkable and I caught a real discrepancy: two separate fetches
of naatak.org both say Bombay Talkies 2 ends **October 4**, not October 10.
Used the verified end date, kept the user-reported day-of-week pattern (noted
in the CSV as user-reported, not independently confirmed, since neither
official page itemizes individual dates), and generated the actual performance
dates programmatically rather than by hand: 16 rows for Pickleball (Thu-Sun,
Aug 20-Sep 13) and 11 for Bombay Talkies 2 (Sat-Sun opening weekend, then
Fri-Sun, Sep 12-Oct 4). Replaced the two old single-date `PLACEHOLDER` rows
with these. Dataset grew from 39 to 64 rows in the process.

Flagged the date discrepancy back to the user rather than silently picking
one version — a case where trusting a verified independent source over a
secondhand recollection was the right call, but transparently, not silently.

**Screenshot:** `screenshots/prompt-8-fixed-calendar.png`

---

## Prompt 9 — Add a missing show (post-submission, live site)

**Context**

After submission, both sites went live (GitHub Pages + Streamlit Community
Cloud). This is the first data update against the deployed, public version.

**Feedback received**

```
I see that Rangmanch still doesn't have all the plays. Calaa.org has some
plays this weekend. but I don't see it on the calendar.
```

**What I did**

Researched calaa.org (California Arts Association, a real Bay Area desi
theater nonprofit founded 2002 — a legitimate source missed in the original
collection pass). Their own site is WebFetch-hostile (JS-rendered, loading
spinners with no static fallback), so I switched to the actual browser tool
to get real rendered content. Found their currently-promoted show, "A
Farewell Dinner" (English adaptation of a French comedy, full cast/director
credited, Historic Hoover Theatre, San Jose) — 5 real performances, Sep 4-6,
with an actual observed seat price ($36.21) from their interactive seat map.

**What I had to push back on**

The show the user described as "this weekend" didn't match what I found —
CalAA's own homepage, upcoming-events page, and year-calendar graphic were
all promoting the September show, not anything for the actual current
weekend. Their year-calendar labels August's slot generically as "Full
Length India Play," but I couldn't find a specific dated listing, venue, or
ticket page for it — their Instagram required login, their Facebook group is
private. Rather than invent an August show to match the report, I added the
one I could fully verify (September) and flagged the gap: I could not
confirm a specific Aug 22-23 CalAA show despite checking their site, search
engines, and public social profiles, and would need a direct link or more
detail to add it accurately.

**What I had to fix**

A self-inflicted bug while wiring the new data into `index.html`: a Python
line-replacement script that swapped in the regenerated `SHOWS` array
dropped the `const SHOWS = ` assignment prefix, leaving a bare array literal
— valid JS syntax, so nothing errored at parse time, but `SHOWS` was
undefined everywhere it was referenced. Caught by loading the page and
checking the console rather than assuming the script worked because it ran
without a Python exception. The console's own error log was also
momentarily misleading — it kept showing the stale pre-fix error after the
fix was live, until I checked `typeof SHOWS` directly in the page instead
of trusting the log.

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
