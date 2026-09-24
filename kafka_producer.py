"""Stream product events to Kafka (topic: ecommerce_events).

Usage (from the repository root):
    python kafka_producer.py            # scrape once, then send one product every 3 seconds
    python kafka_producer.py --sample   # stream the committed sample dataset instead

Kafka must be reachable at KAFKA_BOOTSTRAP_SERVERS (default localhost:9092,
matching docker-compose.yml).
"""
import argparse
import json
import sys
import time

from kafka import KafkaProducer
from kafka.errors import KafkaError

import config
from scrapers.ecommerce_scraper import EcommerceScraper, load_sample


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sample", action="store_true", help="stream data/sample_products.csv")
    parser.add_argument("--interval", type=float, default=3.0, help="seconds between two messages")
    parser.add_argument("--loop", action="store_true", help="restart from the beginning when all products are sent")
    args = parser.parse_args(argv)

    try:
        producer = KafkaProducer(
            bootstrap_servers=config.KAFKA_BOOTSTRAP.split(","),
            value_serializer=lambda payload: json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        )
    except KafkaError as exc:
        print(f"Cannot connect to Kafka at {config.KAFKA_BOOTSTRAP}: {exc}", file=sys.stderr)
        return 1

    products = load_sample() if args.sample else EcommerceScraper().scrape_all()
    if not products:
        print("Nothing to stream (scraping returned no product). Try --sample.", file=sys.stderr)
        return 2
    print(f"Connected to Kafka. Streaming {len(products)} products to '{config.KAFKA_TOPIC}'...")

    sent = 0
    try:
        while True:
            for product in products:
                producer.send(config.KAFKA_TOPIC, value=product)
                sent += 1
                print(f"[producer] {product['name']} | {product['current_price']} DH | {product['source']}")
                time.sleep(args.interval)
            if not args.loop:
                break
    except KeyboardInterrupt:
        pass
    finally:
        producer.flush()
        producer.close()
    print(f"{sent} messages sent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
