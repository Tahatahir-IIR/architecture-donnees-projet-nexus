"""Central configuration for the pipeline.

Every value can be overridden with an environment variable (see .env.example).
Defaults match docker-compose.yml so the pipeline works out of the box on a
local machine where the containers are exposed on localhost.
"""
import os
from pathlib import Path

try:  # optional: load a .env file if python-dotenv is installed
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover
    pass

ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.getenv("DATA_DIR", ROOT_DIR / "data"))

# Local medallion layout (mirrors the MinIO buckets)
BRONZE_DIR = DATA_DIR / "bronze"
SILVER_DIR = DATA_DIR / "silver"
GOLD_DIR = DATA_DIR / "gold"

BRONZE_FILE = BRONZE_DIR / "products_raw.json"
SILVER_FILE = SILVER_DIR / "products_clean.csv"
GOLD_PRODUCT_PRICES = GOLD_DIR / "product_prices.csv"
GOLD_CATEGORY_SUMMARY = GOLD_DIR / "category_summary.csv"
GOLD_SOURCE_COMPARISON = GOLD_DIR / "source_comparison.csv"

SAMPLE_FILE = DATA_DIR / "sample_products.csv"

# MinIO (S3 compatible data lake)
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "admin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "password")

# PostgreSQL warehouse
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "ecommerce_db")
POSTGRES_USER = os.getenv("POSTGRES_USER", "user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")


def postgres_url() -> str:
    """SQLAlchemy URL. DATABASE_URL overrides the individual settings."""
    return os.getenv(
        "DATABASE_URL",
        f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
        f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}",
    )


# Kafka
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "ecommerce_events")
