"""Upload the local bronze / silver / gold files to the matching MinIO buckets.

Usage (from the repository root):
    python upload_medallion.py

Connection settings come from MINIO_ENDPOINT / MINIO_ACCESS_KEY / MINIO_SECRET_KEY
(see .env.example); the defaults match docker-compose.yml.
"""
import sys
from datetime import date

import boto3
from botocore.client import Config
from botocore.exceptions import BotoCoreError, ClientError

import config

LAYERS = [
    ("bronze", config.BRONZE_FILE, "ecommerce/products_raw.json"),
    ("silver", config.SILVER_FILE, "ecommerce/products_clean.csv"),
    ("gold", config.GOLD_PRODUCT_PRICES, "analytics/product_prices.csv"),
    ("gold", config.GOLD_CATEGORY_SUMMARY, "analytics/category_summary.csv"),
    ("gold", config.GOLD_SOURCE_COMPARISON, "analytics/source_comparison.csv"),
]


def s3_client():
    return boto3.client(
        "s3",
        endpoint_url=config.MINIO_ENDPOINT,
        aws_access_key_id=config.MINIO_ACCESS_KEY,
        aws_secret_access_key=config.MINIO_SECRET_KEY,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )


def ensure_bucket(s3, bucket: str):
    try:
        s3.head_bucket(Bucket=bucket)
    except ClientError:
        print(f"Creating bucket '{bucket}'")
        s3.create_bucket(Bucket=bucket)


def upload_medallion_layers() -> int:
    s3 = s3_client()
    partition = f"dt={date.today().isoformat()}"
    failures = 0
    for bucket, path, object_name in LAYERS:
        if not path.exists():
            print(f"Skipping {bucket}/{object_name}: {path} does not exist yet")
            continue
        # Keep a dated copy for history and a "latest" copy for consumers
        folder, _, filename = object_name.rpartition("/")
        keys = [object_name, f"{folder}/{partition}/{filename}"]
        try:
            ensure_bucket(s3, bucket)
            for key in keys:
                s3.upload_file(str(path), bucket, key)
                print(f"Uploaded {path.name} -> {bucket}/{key}")
        except (BotoCoreError, ClientError) as exc:
            failures += 1
            print(f"Upload to {bucket}/{object_name} failed: {exc}", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(upload_medallion_layers())
