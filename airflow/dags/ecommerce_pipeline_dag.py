"""Airflow DAG: run the batch pipeline every hour (scrape -> transform -> MinIO -> PostgreSQL).

The repository is mounted at /opt/airflow/project by docker-compose.yml, and the
airflow service receives MINIO_ENDPOINT / POSTGRES_HOST pointing at the other
containers. Set PIPELINE_ARGS="--sample" in the airflow service environment to
run on the committed sample dataset instead of scraping.
"""
import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

PROJECT_DIR = os.getenv("PROJECT_DIR", "/opt/airflow/project")
SCRAPER_ARGS = os.getenv("PIPELINE_ARGS", "")

default_args = {
    "owner": "taha",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="ecommerce_pipeline",
    description="Jumia / MarjaneMall price monitoring pipeline",
    default_args=default_args,
    start_date=datetime(2026, 1, 1),
    schedule_interval="@hourly",
    catchup=False,
    tags=["ecommerce", "medallion"],
) as dag:

    def step(task_id: str, script: str) -> BashOperator:
        return BashOperator(
            task_id=task_id,
            bash_command=f"cd {PROJECT_DIR} && python {script}",
        )

    scrape = step("scrape_bronze", f"scrapers/ecommerce_scraper.py {SCRAPER_ARGS}")
    transform = step("transform_silver_gold", "etl/transform.py")
    upload = step("upload_minio", "upload_medallion.py")
    load = step("load_postgres", "warehouse/load_postgres.py")

    scrape >> transform >> [upload, load]
