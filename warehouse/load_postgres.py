"""Load the gold layer into the PostgreSQL warehouse.

Usage (from the repository root):
    python warehouse/load_postgres.py
    python warehouse/load_postgres.py --gold-dir data/out/gold

Reads data/gold/product_prices.csv and data/gold/category_summary.csv, creates
the tables from sql/schema.sql if needed, then upserts:
    products         one row per product and source (first_seen / last_seen)
    price_history    one row per product, source and snapshot date
    category_summary one row per category and snapshot date

Connection: POSTGRES_HOST / POSTGRES_PORT / POSTGRES_DB / POSTGRES_USER /
POSTGRES_PASSWORD (defaults match docker-compose.yml), or DATABASE_URL.
"""
import argparse
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402

SCHEMA_FILE = config.ROOT_DIR / "sql" / "schema.sql"

UPSERT_PRODUCTS = text("""
    INSERT INTO products (product_key, source, product_id, name, category, url,
                          stock_status, first_seen, last_seen)
    VALUES (:product_key, :source, :product_id, :name, :category, :url,
            :stock_status, :snapshot_date, :snapshot_date)
    ON CONFLICT (product_key, source) DO UPDATE SET
        product_id   = EXCLUDED.product_id,
        name         = EXCLUDED.name,
        category     = EXCLUDED.category,
        url          = EXCLUDED.url,
        stock_status = EXCLUDED.stock_status,
        last_seen    = EXCLUDED.last_seen
""")

UPSERT_PRICE_HISTORY = text("""
    INSERT INTO price_history (product_key, source, snapshot_date, min_price, avg_price,
                               max_price, n_offers, avg_discount_percent, loaded_at)
    VALUES (:product_key, :source, :snapshot_date, :min_price, :avg_price,
            :max_price, :n_offers, :avg_discount_percent, :loaded_at)
    ON CONFLICT (product_key, source, snapshot_date) DO UPDATE SET
        min_price            = EXCLUDED.min_price,
        avg_price            = EXCLUDED.avg_price,
        max_price            = EXCLUDED.max_price,
        n_offers             = EXCLUDED.n_offers,
        avg_discount_percent = EXCLUDED.avg_discount_percent,
        loaded_at            = EXCLUDED.loaded_at
""")

UPSERT_CATEGORY_SUMMARY = text("""
    INSERT INTO category_summary (category, snapshot_date, n_products, n_offers, n_sources,
                                  min_price, avg_price, max_price, avg_discount_percent, promotions)
    VALUES (:category, :snapshot_date, :n_products, :n_offers, :n_sources,
            :min_price, :avg_price, :max_price, :avg_discount_percent, :promotions)
    ON CONFLICT (category, snapshot_date) DO UPDATE SET
        n_products           = EXCLUDED.n_products,
        n_offers             = EXCLUDED.n_offers,
        n_sources            = EXCLUDED.n_sources,
        min_price            = EXCLUDED.min_price,
        avg_price            = EXCLUDED.avg_price,
        max_price            = EXCLUDED.max_price,
        avg_discount_percent = EXCLUDED.avg_discount_percent,
        promotions           = EXCLUDED.promotions
""")


def apply_schema(conn):
    statements = [s.strip() for s in SCHEMA_FILE.read_text(encoding="utf-8").split(";") if s.strip()]
    for statement in statements:
        conn.execute(text(statement))


def records(df: pd.DataFrame) -> list:
    """DataFrame -> list of dicts with NaN converted to None (SQL NULL)."""
    return df.astype(object).where(df.notna(), None).to_dict(orient="records")


def load(gold_dir: Path, database_url: str | None = None) -> dict:
    prices_path = gold_dir / "product_prices.csv"
    summary_path = gold_dir / "category_summary.csv"
    if not prices_path.exists():
        raise FileNotFoundError(f"{prices_path} not found: run etl/transform.py first")

    prices = pd.read_csv(prices_path)
    prices["loaded_at"] = datetime.now().isoformat(sep=" ", timespec="seconds")
    summary = pd.read_csv(summary_path) if summary_path.exists() else pd.DataFrame()

    engine = create_engine(database_url or config.postgres_url())
    with engine.begin() as conn:
        apply_schema(conn)
        conn.execute(UPSERT_PRODUCTS, records(prices))
        conn.execute(UPSERT_PRICE_HISTORY, records(prices))
        if not summary.empty:
            conn.execute(UPSERT_CATEGORY_SUMMARY, records(summary))
        counts = {
            table: conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            for table in ("products", "price_history", "category_summary")
        }
    engine.dispose()
    return counts


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--gold-dir", type=Path, default=config.GOLD_DIR)
    parser.add_argument("--database-url", default=None, help="SQLAlchemy URL (default: from env)")
    args = parser.parse_args(argv)
    try:
        counts = load(args.gold_dir, args.database_url)
    except Exception as exc:  # connection refused, missing file, ...
        print(f"Postgres load failed: {exc}", file=sys.stderr)
        return 1
    for table, n in counts.items():
        print(f"{table}: {n} rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
