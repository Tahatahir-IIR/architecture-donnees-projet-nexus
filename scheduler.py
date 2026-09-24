"""Lightweight scheduler: run the batch pipeline every hour without Airflow.

Usage (from the repository root):
    python scheduler.py
    python scheduler.py --sample --every 30     # every 30 minutes with the sample dataset
"""
import argparse
import logging
import subprocess
import sys
import time
from pathlib import Path

import schedule

ROOT = Path(__file__).resolve().parent
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("scheduler")


def run_pipeline(extra_args: list) -> None:
    logger.info("Starting scheduled pipeline run")
    result = subprocess.run([sys.executable, "run_full_pipeline.py", *extra_args], cwd=ROOT)
    if result.returncode == 0:
        logger.info("Pipeline run finished")
    else:
        logger.error("Pipeline run failed with exit code %s", result.returncode)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--every", type=int, default=60, help="interval in minutes (default 60)")
    parser.add_argument("--sample", action="store_true", help="pass --sample to the pipeline")
    args = parser.parse_args(argv)

    extra = ["--sample"] if args.sample else []
    run_pipeline(extra)
    schedule.every(args.every).minutes.do(run_pipeline, extra)
    logger.info("Scheduler active: the pipeline runs every %s minutes (Ctrl+C to stop)", args.every)
    try:
        while True:
            schedule.run_pending()
            time.sleep(30)
    except KeyboardInterrupt:
        logger.info("Scheduler stopped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
