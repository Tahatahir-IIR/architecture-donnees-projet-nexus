"""Streamlit dashboard for the e-commerce market intelligence pipeline.

Reads the silver and gold layers produced by etl/transform.py:
    data/silver/products_clean.csv
    data/gold/category_summary.csv
    data/gold/source_comparison.csv

Usage (from the repository root):
    python -m streamlit run dashboard/app.py
The data directory can be changed with the DATA_DIR environment variable.
"""
import os
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

DATA_DIR = Path(os.getenv("DATA_DIR", Path(__file__).resolve().parents[1] / "data"))
SILVER_FILE = DATA_DIR / "silver" / "products_clean.csv"
CATEGORY_FILE = DATA_DIR / "gold" / "category_summary.csv"
COMPARISON_FILE = DATA_DIR / "gold" / "source_comparison.csv"

SOURCE_COLORS = {"Jumia": "#f97316", "MarjaneMall": "#eab308"}
PALETTE = ["#38bdf8", "#818cf8", "#c084fc", "#f472b6", "#34d399", "#fbbf24"]

st.set_page_config(page_title="Market Intelligence", page_icon=":bar_chart:", layout="wide")

st.markdown(
    """
<style>
    .stApp { background-color: #0f111a; color: #e2e8f0; }
    h1, h2, h3, h4 { color: #f8fafc; }
    div[data-testid="metric-container"], .card {
        background: rgba(30, 41, 59, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 16px;
    }
    .card { margin-bottom: 12px; }
    .muted { color: #94a3b8; font-size: 0.85rem; }
    .price { font-size: 1.4rem; font-weight: 700; color: #38bdf8; }
    .offer {
        display: inline-block; margin: 6px 8px 0 0; padding: 4px 10px; border-radius: 6px;
        border: 1px solid #475569; color: #f8fafc; text-decoration: none; font-size: 0.85rem;
    }
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_data(ttl=60)
def load_layer(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    if "scraped_at" in df.columns:
        df["scraped_at"] = pd.to_datetime(df["scraped_at"], errors="coerce")
    return df


def plotly_dark(fig, height=380):
    fig.update_layout(template="plotly_dark", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                      height=height, margin=dict(l=0, r=0, t=30, b=0))
    return fig


silver = load_layer(SILVER_FILE)
category_summary = load_layer(CATEGORY_FILE)
comparison = load_layer(COMPARISON_FILE)

st.title("E-commerce Market Intelligence")
st.markdown(
    f"<span class='muted'>Jumia and MarjaneMall price monitoring. Data directory: {DATA_DIR} "
    f"| Page loaded at {datetime.now():%Y-%m-%d %H:%M:%S}</span>",
    unsafe_allow_html=True,
)

if silver.empty:
    st.warning(
        "No silver data found. Run the pipeline first, for example: "
        "`python run_full_pipeline.py --sample --skip-minio --skip-postgres`"
    )
    st.stop()

# ----------------------------------------------------------------------------- filters
st.sidebar.header("Filters")
categories = ["All"] + sorted(silver["category"].dropna().unique().tolist())
selected_category = st.sidebar.selectbox("Category", categories)
all_sources = sorted(silver["source"].dropna().unique().tolist())
selected_sources = st.sidebar.multiselect("Sources", all_sources, default=all_sources)
price_min, price_max = int(silver["current_price"].min()), int(silver["current_price"].max())
price_range = st.sidebar.slider("Price range (DH)", price_min, price_max, (price_min, price_max))
search = st.sidebar.text_input("Search a product")
only_promotions = st.sidebar.checkbox("Promotions only")

df = silver.copy()
if selected_category != "All":
    df = df[df["category"] == selected_category]
df = df[df["source"].isin(selected_sources)]
df = df[(df["current_price"] >= price_range[0]) & (df["current_price"] <= price_range[1])]
if search:
    df = df[df["name"].str.contains(search, case=False, na=False)]
if only_promotions:
    df = df[df["is_promotion"] == True]  # noqa: E712

if df.empty:
    st.info("No offer matches the current filters.")
    st.stop()

tab_overview, tab_compare, tab_recent, tab_tables = st.tabs(
    ["Overview", "Price comparison", "Latest offers", "Gold tables"]
)

# ----------------------------------------------------------------------------- overview
with tab_overview:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Offers", f"{len(df):,}")
    c2.metric("Distinct products", f"{df['product_key'].nunique():,}")
    c3.metric("Average price", f"{df['current_price'].mean():,.0f} DH")
    c4.metric("Promotions", f"{int(df['is_promotion'].sum()):,}")

    left, right = st.columns([3, 2])
    with left:
        fig = px.histogram(df, x="current_price", color="category", nbins=30, marginal="box",
                           title="Price distribution", labels={"current_price": "Price (DH)"},
                           color_discrete_sequence=PALETTE)
        st.plotly_chart(plotly_dark(fig), use_container_width=True)
    with right:
        fig = px.sunburst(df, path=["source", "category"], values="current_price",
                          title="Catalogue value by source and category", color_discrete_sequence=PALETTE)
        st.plotly_chart(plotly_dark(fig), use_container_width=True)

    left, right = st.columns(2)
    with left:
        avg = df.groupby(["category", "source"], as_index=False)["current_price"].mean()
        fig = px.bar(avg, x="category", y="current_price", color="source", barmode="group",
                     title="Average price per category and source", labels={"current_price": "Average price (DH)"},
                     color_discrete_map=SOURCE_COLORS)
        st.plotly_chart(plotly_dark(fig, 340), use_container_width=True)
    with right:
        fig = px.scatter(df, x="current_price", y="category", color="source", size="current_price",
                         hover_name="name", title="Offers by category", labels={"current_price": "Price (DH)"},
                         color_discrete_map=SOURCE_COLORS)
        st.plotly_chart(plotly_dark(fig, 340), use_container_width=True)

# ----------------------------------------------------------------------------- comparison
with tab_compare:
    st.markdown("One card per product, with the price found on each source (from gold/source_comparison.csv).")
    if comparison.empty:
        st.info("gold/source_comparison.csv not found.")
    else:
        keys = set(df["product_key"])
        cmp_df = comparison[comparison["product_key"].isin(keys)].sort_values("best_price")
        multi = cmp_df[cmp_df["n_sources"] > 1]
        m1, m2, m3 = st.columns(3)
        m1.metric("Products compared", f"{len(cmp_df):,}")
        m2.metric("Available on both sources", f"{len(multi):,}")
        m3.metric("Average price gap", f"{multi['price_gap_percent'].mean():.1f} %" if not multi.empty else "n/a")

        offers_by_key = {k: g for k, g in df.groupby("product_key")}
        for _, row in cmp_df.head(40).iterrows():
            offers = offers_by_key.get(row["product_key"], pd.DataFrame())
            offers_html = ""
            for _, offer in offers.sort_values("current_price").iterrows():
                color = SOURCE_COLORS.get(offer["source"], "#3b82f6")
                offers_html += (
                    f"<a class='offer' href='{offer['url']}' target='_blank' style='border-color:{color};'>"
                    f"{offer['source']}: <strong style='color:{color};'>{offer['current_price']:,.0f} DH</strong></a>"
                )
            gap = f" | gap {row['price_gap']:,.0f} DH ({row['price_gap_percent']:.1f} %)" if row["n_sources"] > 1 else ""
            st.markdown(
                f"<div class='card'><strong>{row['name']}</strong>"
                f"<div class='muted'>{row['category']} | cheapest: {row['cheapest_source']}{gap}</div>"
                f"<span class='price'>{row['best_price']:,.0f} DH</span><div>{offers_html}</div></div>",
                unsafe_allow_html=True,
            )

# ----------------------------------------------------------------------------- recent
with tab_recent:
    recent = df.sort_values("scraped_at", ascending=False).head(15)
    for _, row in recent.iterrows():
        when = row["scraped_at"].strftime("%Y-%m-%d %H:%M") if pd.notna(row["scraped_at"]) else "unknown time"
        promo = f" | -{row['discount_percent']:.0f} %" if row["is_promotion"] else ""
        st.markdown(
            f"<div class='card'><strong>{row['name']}</strong>"
            f"<div class='muted'>{row['source']} | {row['category']} | scraped {when}</div>"
            f"<span class='price'>{row['current_price']:,.0f} DH</span>{promo} "
            f"<a class='offer' href='{row['url']}' target='_blank'>open</a></div>",
            unsafe_allow_html=True,
        )

# ----------------------------------------------------------------------------- tables
with tab_tables:
    st.subheader("Category summary")
    st.dataframe(category_summary, use_container_width=True, hide_index=True)
    st.subheader("Source comparison")
    st.dataframe(comparison, use_container_width=True, hide_index=True)
    st.subheader("Silver offers (filtered)")
    st.dataframe(df, use_container_width=True, hide_index=True)
