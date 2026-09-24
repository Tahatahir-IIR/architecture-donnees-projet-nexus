"""Pandas transformation: bronze (raw scrape) -> silver (clean) -> gold (aggregates).

Usage (from the repository root):
    python etl/transform.py                       # data/bronze/products_raw.json -> data/silver, data/gold
    python etl/transform.py --input data/sample_products.csv --output-dir data/out

The silver layer is a cleaned, deduplicated table of product offers.
The gold layer contains three analytical tables:
    product_prices.csv     one row per product and source (min/avg/max price)
    category_summary.csv   one row per category
    source_comparison.csv  one row per product with the price on each source
"""
import argparse
import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402

REQUIRED_COLUMNS = [
    "product_id", "name", "category", "current_price", "original_price",
    "currency", "source", "url", "stock_status", "timestamp",
]

SOURCE_ALIASES = {
    "jumia": "Jumia",
    "jumia.ma": "Jumia",
    "marjanemall": "MarjaneMall",
    "marjane mall": "MarjaneMall",
    "marjane": "MarjaneMall",
    "marjanemall.ma": "MarjaneMall",
}


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def parse_price(value):
    """Convert '4 099,00 DH', '1,299 Dhs', 1299 or '1299.5' to a float (or NaN)."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return float("nan")
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text:
        return float("nan")
    text = re.sub(r"(?i)dhs?|mad", "", text)
    text = re.sub(r"[\s\xa0]", "", text)
    # "4099,00" -> decimal comma; "1,299" -> thousands separator
    if "," in text and "." not in text:
        head, _, tail = text.rpartition(",")
        text = f"{head}.{tail}" if len(tail) == 2 else text.replace(",", "")
    else:
        text = text.replace(",", "")
    try:
        return float(text)
    except ValueError:
        return float("nan")


def normalise_source(value) -> str:
    key = re.sub(r"\s+", " ", str(value or "")).strip().lower()
    return SOURCE_ALIASES.get(key, key.replace(" ", "").title() if key else "Unknown")


def product_key(name: str, category: str) -> str:
    """Deterministic identifier shared by the same product on every source."""
    basis = f"{name.lower()}|{category.lower()}".encode("utf-8")
    return hashlib.md5(basis).hexdigest()[:16]


def read_bronze(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".json":
        with open(path, "r", encoding="utf-8") as fh:
            return pd.DataFrame(json.load(fh))
    return pd.read_csv(path, dtype=str, keep_default_na=False)


# --------------------------------------------------------------------------- #
# Silver
# --------------------------------------------------------------------------- #
def build_silver(df_raw: pd.DataFrame) -> pd.DataFrame:
    df = df_raw.copy()
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            df[col] = None

    # Trim strings
    for col in ["product_id", "name", "category", "currency", "source", "url", "stock_status"]:
        df[col] = df[col].astype("string").str.strip().fillna("")

    df["source"] = df["source"].map(normalise_source)
    df["currency"] = df["currency"].replace({"": "DH", "Dhs": "DH", "MAD": "DH"})
    df["stock_status"] = df["stock_status"].replace({"": "Unknown", "In Stock": "En Stock"})

    df["current_price"] = df["current_price"].map(parse_price)
    df["original_price"] = df["original_price"].map(parse_price)
    df["original_price"] = df["original_price"].fillna(df["current_price"])
    df.loc[df["original_price"] < df["current_price"], "original_price"] = df["current_price"]

    # Drop rows without a usable price or name
    df = df[(df["name"] != "") & df["current_price"].notna() & (df["current_price"] > 0)]

    df["discount_percent"] = ((1 - df["current_price"] / df["original_price"]) * 100).round(1)
    df["is_promotion"] = df["discount_percent"] > 0
    df["scraped_at"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["product_key"] = [product_key(n, c) for n, c in zip(df["name"], df["category"])]

    # One offer per product and source: keep the most recent scrape
    df = (
        df.sort_values("scraped_at", ascending=False, na_position="last")
        .drop_duplicates(subset=["product_key", "source"], keep="first")
        .sort_values(["category", "name", "source"])
        .reset_index(drop=True)
    )
    df["processed_at"] = pd.Timestamp.now().isoformat(timespec="seconds")

    columns = [
        "product_key", "product_id", "name", "category", "source", "current_price",
        "original_price", "discount_percent", "is_promotion", "currency", "url",
        "stock_status", "scraped_at", "processed_at",
    ]
    return df[columns]


# --------------------------------------------------------------------------- #
# Gold
# --------------------------------------------------------------------------- #
def build_gold(silver: pd.DataFrame, snapshot_date: date | None = None) -> dict:
    snapshot_date = snapshot_date or date.today()

    product_prices = (
        silver.groupby(["product_key", "name", "category", "source"], as_index=False)
        .agg(
            product_id=("product_id", "first"),
            min_price=("current_price", "min"),
            avg_price=("current_price", "mean"),
            max_price=("current_price", "max"),
            n_offers=("current_price", "size"),
            avg_discount_percent=("discount_percent", "mean"),
            url=("url", "first"),
            stock_status=("stock_status", "first"),
        )
    )
    product_prices["avg_price"] = product_prices["avg_price"].round(2)
    product_prices["avg_discount_percent"] = product_prices["avg_discount_percent"].round(1)
    product_prices["snapshot_date"] = snapshot_date.isoformat()

    category_summary = (
        silver.groupby("category", as_index=False)
        .agg(
            n_products=("product_key", "nunique"),
            n_offers=("product_key", "size"),
            n_sources=("source", "nunique"),
            min_price=("current_price", "min"),
            avg_price=("current_price", "mean"),
            max_price=("current_price", "max"),
            avg_discount_percent=("discount_percent", "mean"),
            promotions=("is_promotion", "sum"),
        )
    )
    category_summary["avg_price"] = category_summary["avg_price"].round(2)
    category_summary["avg_discount_percent"] = category_summary["avg_discount_percent"].round(1)
    category_summary["snapshot_date"] = snapshot_date.isoformat()

    # Per-source comparison: one column per source, cheapest source and price gap
    pivot = silver.pivot_table(
        index=["product_key", "name", "category"], columns="source",
        values="current_price", aggfunc="min",
    )
    source_of_column = {f"price_{c.lower()}": c for c in pivot.columns}
    pivot.columns = list(source_of_column)
    price_cols = list(pivot.columns)
    comparison = pivot.reset_index()
    comparison["n_sources"] = comparison[price_cols].notna().sum(axis=1)
    comparison["best_price"] = comparison[price_cols].min(axis=1)
    comparison["cheapest_source"] = comparison[price_cols].idxmin(axis=1).map(source_of_column)
    comparison["price_gap"] = (comparison[price_cols].max(axis=1) - comparison["best_price"]).round(2)
    comparison["price_gap_percent"] = (
        comparison["price_gap"] / comparison["best_price"] * 100
    ).round(1)
    comparison["snapshot_date"] = snapshot_date.isoformat()
    comparison = comparison.sort_values(["category", "name"]).reset_index(drop=True)

    return {
        "product_prices": product_prices,
        "category_summary": category_summary,
        "source_comparison": comparison,
    }


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def run(input_path: Path, output_dir: Path | None = None) -> dict:
    if output_dir is None:
        silver_path = config.SILVER_FILE
        gold_dir = config.GOLD_DIR
    else:
        silver_path = output_dir / "silver" / "products_clean.csv"
        gold_dir = output_dir / "gold"
    silver_path.parent.mkdir(parents=True, exist_ok=True)
    gold_dir.mkdir(parents=True, exist_ok=True)

    raw = read_bronze(input_path)
    print(f"[bronze] {len(raw)} raw rows read from {input_path}")

    silver = build_silver(raw)
    silver.to_csv(silver_path, index=False, encoding="utf-8")
    print(f"[silver] {len(silver)} clean offers -> {silver_path}")

    gold = build_gold(silver)
    for name, frame in gold.items():
        path = gold_dir / f"{name}.csv"
        frame.to_csv(path, index=False, encoding="utf-8")
        print(f"[gold]   {name}: {len(frame)} rows -> {path}")

    print("\nCategory summary:")
    print(gold["category_summary"].to_string(index=False))
    return {"silver": silver, **gold}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", type=Path, default=config.BRONZE_FILE,
                        help="bronze JSON or CSV file (default: data/bronze/products_raw.json)")
    parser.add_argument("--output-dir", type=Path, default=None,
                        help="write silver/ and gold/ under this directory instead of data/")
    args = parser.parse_args(argv)
    if not args.input.exists():
        print(f"Input file not found: {args.input}", file=sys.stderr)
        return 1
    run(args.input, args.output_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
