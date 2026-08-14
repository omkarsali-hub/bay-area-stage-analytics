# Dataset collection guide

## Schema

One row = **one performance on one date.** A play running three nights is three rows.
This matters: saturation and seasonality analysis both need per-date granularity.

| Column | Type | Rules |
|---|---|---|
| `show_title` | text | As advertised. Don't translate or clean up. |
| `company` | text | The producing company or presenter. Keep spelling consistent — this is your group-by key. |
| `language` | text | Marathi / Hindi / Gujarati / Tamil / Telugu / Bengali / Hinglish / English / Multilingual. Leave blank if unsure, never guess. |
| `genre` | text | Play / Musical / Standup / Dance / Other. |
| `venue` | text | Venue name only, no address. |
| `city` | text | e.g. Milpitas, Fremont, Campbell. |
| `region` | text | South Bay / East Bay / Peninsula / SF / North Bay. |
| `date` | `YYYY-MM-DD` | Always this format. No exceptions — this is where CSVs go wrong. |
| `start_time` | `HH:MM` | 24-hour. Blank if not listed. |
| `price_min` | number | Lowest list price. `0` for free. Blank if genuinely unknown. |
| `price_max` | number | Highest list price. Same as `price_min` if single price. |
| `ticketing_platform` | text | Eventbrite / Sulekha / Ticketleap / Zeffy / Own site / Free entry. |
| `source_url` | url | Where you found it. **Required on every row.** |
| `collected_on` | `YYYY-MM-DD` | The day you collected it. |
| `notes` | text | Anything uncertain. Flag placeholders here. |

### Rules

1. **Never invent a value.** Blank beats a guess. `price_min` blank is honest;
   `price_min = 25` because it felt right is data fraud in a graded project.
2. **Every row needs a `source_url`.** If you can't cite it, don't add it.
3. Prefix anything unverified with `PLACEHOLDER` in `notes` and either confirm it or
   delete it before submitting.
4. Keep `company` spelling identical across rows. "Naatak" and "Naatak Theatre" become
   two companies in a group-by and quietly wreck the analysis.

## Collect backwards, not forwards

**Aim for roughly Sept 2025 through Dec 2026.**

Only collecting upcoming shows gives you ~30 rows and no seasonality at all. A rolling
year of past shows gives you festival clustering (Ganesh Chaturthi, Navratri, Diwali,
Gudi Padwa), real weekend collisions, and pricing you can actually compare. Past events
are also easier to find because they've been listed, reviewed and archived.

Target: **60–100 rows.** That's enough for every chart in the app to say something real.

## Sources, in order of yield

### 1. Sulekha Events — highest yield by far

Aggregates Indian community events by language and metro. Has a past-events section.

- Marathi: `https://events.sulekha.com/upcoming-marathi-events-tickets-bay-area`
- Hindi: `https://events.sulekha.com/upcoming-hindi-events-tickets-bay-area`
- Gujarati: `https://events.sulekha.com/upcoming-gujarati-events-tickets-bay-area`
- Bay Area, all: `https://ca.sulekha.com/events-bay-area`
- Santa Clara: `https://ca.sulekha.com/events-santa-clara-ca`

Swap the language in the URL for Tamil, Telugu, Bengali, Punjabi. Filter to
**Drama** and **Comedy** categories — skip the concerts, garba nights and food
festivals unless you decide to include them as a comparison category.

### 2. Company websites

Naatak (`naatak.org`) publishes full seasons with dates and venues — best structured
source you'll find. Then work through the companies you already know: Marathi mandals,
Gujarati samaj groups, Tamil sangams, and the local comedy collectives.

### 3. Eventbrite

Search "Bay Area" + natak / drama / desi comedy / Marathi / Gujarati. Filter by past
dates too.

### 4. India Currents

`indiacurrents.com` covers and reviews Bay Area South Asian theater. Good for finding
productions that never got a proper listing anywhere.

### 5. English community theater (comparison set)

Add 10–15 rows from non-desi Bay Area community theaters. This gives you a baseline
to compare pricing against, and it's the most interesting chart in the whole app.

## Time-box it

Two hours, in this order. Stop when the timer goes, whatever you have.

| Time | Task |
|---|---|
| 0:00–0:45 | Sulekha, all languages, Drama + Comedy, past and upcoming |
| 0:45–1:15 | Naatak full seasons + 3–4 company sites you know |
| 1:15–1:35 | Eventbrite desi comedy and open mics |
| 1:35–1:50 | English community theater comparison rows |
| 1:50–2:00 | Clean: check date formats, dedupe, standardise company names |

## Before you commit

```bash
python -c "
import pandas as pd
d = pd.read_csv('data/shows.csv')
print('rows:', len(d))
print(d['date'].pipe(pd.to_datetime, errors='coerce').isna().sum(), 'bad dates')
print('companies:', sorted(d['company'].dropna().unique()))
print('missing source_url:', d['source_url'].isna().sum())
"
```

Bad dates and near-duplicate company names are the two things that will silently
break every chart.
