import json
import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Bay Area Stage Analytics", page_icon="🎭", layout="wide")

# ---------------------------------------------------------------------------
# Design tokens (dark mode) - see dataviz skill reference palette
# ---------------------------------------------------------------------------
SURFACE = "#1a1a19"
PAGE_PLANE = "#0d0d0d"
INK_PRIMARY = "#ffffff"
INK_SECONDARY = "#c3c2b7"
INK_MUTED = "#898781"
GRIDLINE = "#2c2c2a"
BASELINE = "#383835"
STATUS_CRITICAL = "#d03b3b"

# Fixed categorical order (never cycled) - first five slots of the validated
# 8-hue dark palette: blue, orange, aqua, yellow, magenta.
GENRE_COLORS = {
    "Play": "#3987e5",
    "Musical": "#d95926",
    "Standup": "#199e70",
    "Dance": "#c98500",
    "Other": "#d55181",
}
COLLISION_COLORS = {True: STATUS_CRITICAL, False: INK_MUTED}

CUSTOM_CSS = f"""
<style>
    .block-container {{
        padding-top: 2rem;
        max-width: 1200px;
    }}
    h1 {{
        font-size: 2.1rem !important;
    }}
    .app-subtitle {{
        color: {INK_SECONDARY};
        margin-top: -0.6rem;
        margin-bottom: 1.2rem;
        font-size: 0.95rem;
    }}
    [data-testid="stMetric"] {{
        background: {SURFACE};
        border: 1px solid {BASELINE};
        border-radius: 10px;
        padding: 0.9rem 1rem 0.7rem 1rem;
    }}
    [data-testid="stMetricLabel"] {{
        color: {INK_MUTED};
    }}
    .stTabs [data-baseweb="tab-list"] {{
        gap: 4px;
    }}
    .stTabs [data-baseweb="tab"] {{
        padding: 0.5rem 1rem;
    }}
    [data-testid="stSidebar"] {{
        border-right: 1px solid {BASELINE};
    }}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def themed(fig: go.Figure) -> go.Figure:
    """Apply the shared dark chart theme (surfaces, ink, gridlines) to a figure."""
    fig.update_layout(
        paper_bgcolor=SURFACE,
        plot_bgcolor=SURFACE,
        font=dict(color=INK_SECONDARY, family="system-ui, -apple-system, 'Segoe UI', sans-serif"),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        margin=dict(t=40, l=10, r=10, b=10),
    )
    fig.update_xaxes(gridcolor=GRIDLINE, linecolor=BASELINE, zerolinecolor=BASELINE, color=INK_MUTED)
    fig.update_yaxes(gridcolor=GRIDLINE, linecolor=BASELINE, zerolinecolor=BASELINE, color=INK_MUTED)
    return fig


SCHEMA_COLUMNS = [
    "show_title", "company", "language", "genre", "venue", "city", "region",
    "date", "start_time", "price_min", "price_max", "ticketing_platform",
    "source_url", "notes",
]


def extract_show(raw_text: str, api_key: str) -> dict:
    client = Anthropic(api_key=api_key)
    prompt = f"""Extract structured show data from this raw announcement text.

Return ONLY a JSON object (no markdown fences, no commentary) with exactly these keys:
{SCHEMA_COLUMNS}

Rules:
- Never invent a value. Use null for anything not explicitly stated in the text.
- "date" must be YYYY-MM-DD, or null if not stated.
- "start_time" must be 24-hour HH:MM, or null.
- "language" must be one of: Marathi, Hindi, Gujarati, Tamil, Telugu, Bengali, Hinglish, English, Multilingual — or null if unclear.
- "genre" must be one of: Play, Musical, Standup, Dance, Other.
- "price_min" and "price_max" are numbers, or null.

Text:
\"\"\"{raw_text}\"\"\"
"""
    response = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text)


st.title("🎭 Bay Area Stage Analytics")
st.markdown(
    '<div class="app-subtitle">Where Bay Area desi theater and standup collide — '
    "pricing, venues, dates, and companies, in one place.</div>",
    unsafe_allow_html=True,
)


@st.cache_data
def load_data(path: str = "data/shows.csv") -> pd.DataFrame:
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["day_of_week"] = df["date"].dt.day_name()
    df["month"] = df["date"].dt.month_name()
    return df


df = load_data()

# Blank category values (e.g. unconfirmed language on a placeholder row) would
# otherwise silently drop out of every isin() filter below, even "select all".
FILTER_COLUMNS = ["language", "genre", "region", "company"]
for col in FILTER_COLUMNS:
    df[col] = df[col].fillna("Unknown")

st.sidebar.header("🔎 Filters")


def multiselect_filter(label: str, column: str) -> list[str]:
    options = sorted(df[column].unique())
    return st.sidebar.multiselect(label, options, default=options)


languages = multiselect_filter("Language", "language")
genres = multiselect_filter("Genre", "genre")
regions = multiselect_filter("Region", "region")
companies = multiselect_filter("Company", "company")

min_date, max_date = df["date"].min().date(), df["date"].max().date()
date_range = st.sidebar.date_input(
    "Date range", value=(min_date, max_date), min_value=min_date, max_value=max_date
)
if len(date_range) != 2:
    date_range = (min_date, max_date)
start_date, end_date = date_range

mask = (
    df["language"].isin(languages)
    & df["genre"].isin(genres)
    & df["region"].isin(regions)
    & df["company"].isin(companies)
    & (df["date"].dt.date >= start_date)
    & (df["date"].dt.date <= end_date)
)
filtered = df[mask]

st.caption(f"{len(filtered)} of {len(df)} shows match the current filters")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Shows", len(filtered))
col2.metric("Companies", filtered["company"].nunique())
col3.metric("Venues", filtered["venue"].nunique())
col4.metric("Languages", filtered["language"].nunique())

st.write("")

MONTH_ORDER = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

tab_price, tab_venue, tab_saturation, tab_season, tab_company, tab_ai = st.tabs(
    [
        "💰 Price distribution",
        "📍 Venue concentration",
        "📅 Weekend saturation",
        "🍂 Seasonality",
        "🏢 Company activity",
        "🤖 AI extract",
    ]
)

with tab_price:
    priced = filtered.dropna(subset=["price_min", "price_max"]).copy()
    skipped = len(filtered) - len(priced)
    if skipped:
        st.caption(f"{skipped} shows have no listed price and are excluded from this chart.")
    if priced.empty:
        st.info("No priced shows in the current filter selection.")
    else:
        priced["price_mid"] = (priced["price_min"] + priced["price_max"]) / 2
        fig = px.box(
            priced,
            x="language",
            y="price_mid",
            color="genre",
            points="all",
            hover_data=["show_title", "company", "price_min", "price_max"],
            labels={"price_mid": "Ticket price ($)", "language": "Language"},
            color_discrete_map=GENRE_COLORS,
            category_orders={"genre": list(GENRE_COLORS)},
        )
        st.plotly_chart(themed(fig), width="stretch")

with tab_venue:
    if filtered.empty:
        st.info("No shows in the current filter selection.")
    else:
        by_venue = (
            filtered["venue"].fillna("Unknown / not listed").value_counts().reset_index()
        )
        by_venue.columns = ["venue", "shows"]
        fig = px.bar(
            by_venue.sort_values("shows"),
            x="shows",
            y="venue",
            orientation="h",
            labels={"shows": "Number of shows", "venue": "Venue"},
            color_discrete_sequence=[GENRE_COLORS["Play"]],
        )
        st.plotly_chart(themed(fig), width="stretch")

with tab_saturation:
    if filtered.empty:
        st.info("No shows in the current filter selection.")
    else:
        by_date = filtered.groupby(filtered["date"].dt.date).size().reset_index()
        by_date.columns = ["date", "shows"]
        by_date["is_collision"] = by_date["shows"] > 1
        fig = px.bar(
            by_date,
            x="date",
            y="shows",
            color="is_collision",
            color_discrete_map=COLLISION_COLORS,
            labels={"shows": "Shows that day", "date": "Date", "is_collision": "2+ shows same day"},
        )
        st.plotly_chart(themed(fig), width="stretch")

        collisions = by_date[by_date["is_collision"]].sort_values("date")
        if collisions.empty:
            st.caption("No same-day collisions in the current filter selection.")
        else:
            st.write("**Dates with 2+ shows competing for the same audience:**")
            for _, row in collisions.iterrows():
                same_day = filtered[filtered["date"].dt.date == row["date"]]
                titles = ", ".join(
                    f"{r.show_title} ({r.company})" for r in same_day.itertuples()
                )
                st.write(f"- {row['date']}: {titles}")

with tab_season:
    if filtered.empty:
        st.info("No shows in the current filter selection.")
    else:
        by_month = filtered["month"].value_counts().reindex(MONTH_ORDER, fill_value=0).reset_index()
        by_month.columns = ["month", "shows"]
        fig = px.bar(
            by_month, x="month", y="shows",
            labels={"shows": "Number of shows", "month": "Month"},
            color_discrete_sequence=[GENRE_COLORS["Musical"]],
        )
        st.plotly_chart(themed(fig), width="stretch")
        st.caption(
            "Bay Area desi festival season (Ganesh Chaturthi, Navratri, Diwali) typically "
            "falls Aug–Nov; watch this chart for that cluster as the dataset grows."
        )

with tab_company:
    if filtered.empty:
        st.info("No shows in the current filter selection.")
    else:
        activity = (
            filtered.groupby("company")
            .agg(shows=("show_title", "count"), last_show=("date", "max"), first_show=("date", "min"))
            .reset_index()
            .sort_values("shows", ascending=False)
        )
        fig = px.bar(
            activity,
            x="shows",
            y="company",
            orientation="h",
            labels={"shows": "Number of shows", "company": "Company"},
            color_discrete_sequence=[GENRE_COLORS["Standup"]],
        )
        st.plotly_chart(themed(fig), width="stretch")
        st.write("**Most recent show per company** (a company far from today's date has gone quiet):")
        st.dataframe(
            activity[["company", "shows", "first_show", "last_show"]].sort_values("last_show"),
            hide_index=True,
        )

with tab_ai:
    st.write(
        "Paste a raw show announcement (Instagram caption, event listing, etc.) and "
        "Claude will pull it into a row matching the dataset schema. Nothing is "
        "invented — any field the text doesn't state comes back `null`."
    )
    raw_text = st.text_area("Raw announcement", height=200)
    if st.button("Extract with Claude"):
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            st.error(
                "No ANTHROPIC_API_KEY found. Set it in a .env file or your shell "
                "environment to use this panel."
            )
        elif not raw_text.strip():
            st.warning("Paste some announcement text first.")
        else:
            with st.spinner("Extracting..."):
                try:
                    row = extract_show(raw_text, api_key)
                    st.success("Extracted — review before adding to the dataset:")
                    st.json(row)
                except json.JSONDecodeError:
                    st.error("Claude's response wasn't valid JSON. Try again or simplify the text.")
                except Exception as e:
                    st.error(f"Extraction failed: {e}")
