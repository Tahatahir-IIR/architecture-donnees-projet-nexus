"""Consume product events from Kafka and print price alerts.

Usage (from the repository root):
    python kafka_consumer.py
    python kafka_consumer.py --threshold 500      # alert when a price is below 500 DH
"""
import argparse
import json
import logging
import sys

from kafka import KafkaConsumer
from kafka.errors import KafkaError

import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("kafka_consumer")


def to_float(value) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--threshold", type=float, default=100.0, help="price alert threshold in DH")
    parser.add_argument("--discount", type=float, default=20.0, help="discount alert threshold in percent")
    args = parser.parse_args(argv)

    try:
        consumer = KafkaConsumer(
            config.KAFKA_TOPIC,
            bootstrap_servers=config.KAFKA_BOOTSTRAP.split(","),
            auto_offset_reset="earliest",
            enable_auto_commit=True,
            group_id="ecommerce-monitoring-group",
            value_deserializer=lambda raw: json.loads(raw.decode("utf-8")),
        )
    except KafkaError as exc:
        logger.error("Cannot connect to Kafka at %s: %s", config.KAFKA_BOOTSTRAP, exc)
        return 1

    logger.info("Consumer started on topic '%s', waiting for events...", config.KAFKA_TOPIC)
    try:
        for message in consumer:
            product = message.value
            price = to_float(product.get("current_price"))
            discount = to_float(product.get("discount_percent"))
            logger.info("%s | %.2f DH | %s | %s",
                        product.get("name", "?"), price, product.get("source", "?"), product.get("category", "?"))
            if 0 < price < args.threshold:
                logger.warning("PRICE ALERT: %s at %.2f DH", product.get("name"), price)
            if discount >= args.discount:
                logger.warning("PROMOTION ALERT: %s at -%.0f%%", product.get("name"), discount)
    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
