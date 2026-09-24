"""Run the batch pipeline end to end: scrape -> transform -> MinIO -> PostgreSQL.

Usage (from the repository root):
    python run_full_pipeline.py                 # live scraping, all steps
    python run_full_pipeline.py --sample        # use data/sample_products.csv instead of scraping
    python run_full_pipeline.py --sample --skip-minio --skip-postgres   # offline check
    python run_full_pipeline.py --dashboard     # also start the Streamlit dashboard at the end

Each step is a separate script executed with subprocess.run; the pipeline stops
at the first step that exits with a non-zero code. Works on Windows, Linux and macOS.
"""
import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def run_step(label: str, command: list) -> None:
    print(f"\n=== {label} ===")
    print("$", " ".join(command))
    started = time.time()
    result = subprocess.run(command, cwd=ROOT)
    if result.returncode != 0:
        print(f"Step '{label}' failed with exit code {result.returncode}", file=sys.stderr)
        sys.exit(result.returncode)
    print(f"Step '{label}' finished in {time.time() - started:.1f}s")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sample", action="store_true", help="use the committed sample dataset")
    parser.add_argument("--skip-minio", action="store_true", help="do not upload to MinIO")
    parser.add_argument("--skip-postgres", action="store_true", help="do not load PostgreSQL")
    parser.add_argument("--dashboard", action="store_true", help="start the Streamlit dashboard afterwards")
    args = parser.parse_args(argv)

    python = sys.executable

    scrape_cmd = [python, "scrapers/ecommerce_scraper.py"]
    if args.sample:
        scrape_cmd.append("--sample")
    run_step("1/4 Scraping (bronze)", scrape_cmd)
    run_step("2/4 Transformation (silver + gold)", [python, "etl/transform.py"])
    if args.skip_minio:
        print("\n=== 3/4 MinIO upload skipped ===")
    else:
        run_step("3/4 Data lake upload (MinIO)", [python, "upload_medallion.py"])
    if args.skip_postgres:
        print("\n=== 4/4 PostgreSQL load skipped ===")
    else:
        run_step("4/4 Warehouse load (PostgreSQL)", [python, "warehouse/load_postgres.py"])

    print("\nPipeline completed.")
    if args.dashboard:
        print("Starting the dashboard on http://localhost:8501 (Ctrl+C to stop)")
        return subprocess.run([python, "-m", "streamlit", "run", "dashboard/app.py"], cwd=ROOT).returncode
    print("Dashboard: python -m streamlit run dashboard/app.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
