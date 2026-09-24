"""Scrape product listings from Jumia Maroc and MarjaneMall into the bronze layer.

Usage (from the repository root):
    python scrapers/ecommerce_scraper.py            # live scraping -> data/bronze/products_raw.json
    python scrapers/ecommerce_scraper.py --sample   # copy data/sample_products.csv into bronze instead

Only products that were actually found on the sites are written. Nothing is
generated or duplicated: if a site blocks the request (HTTP 403 from the
anti-bot protection is common) the run simply returns fewer rows, and the
--sample flag can be used to exercise the rest of the pipeline.
"""
import argparse
import hashlib
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
}

# (category label, Jumia path, MarjaneMall path)
TARGETS = [
    ("Informatique", "ordinateurs-portables/", "informatique/ordinateurs-portables"),
    ("Smartphones", "smartphones/", "telephonie/smartphones"),
    ("Électroménager", "refrigerateurs/", "electromenager/refrigerateurs-congelateurs"),
    ("TV & Audio", "televiseurs/", "image-et-son/televiseurs"),
    ("Mode", "mode-homme/", "mode/homme"),
]


def parse_price(text: str):
    """'1,299 Dhs' / '4 099,00 DH' -> float, or None."""
    if not text:
        return None
    cleaned = re.sub(r"(?i)dhs?|mad", "", text)
    cleaned = re.sub(r"[\s\xa0]", "", cleaned)
    if "," in cleaned and "." not in cleaned:
        head, _, tail = cleaned.rpartition(",")
        cleaned = f"{head}.{tail}" if len(tail) == 2 else cleaned.replace(",", "")
    cleaned = cleaned.replace(",", "")
    try:
        return float(cleaned)
    except ValueError:
        return None


def make_id(source: str, url: str) -> str:
    return f"{source[:3].upper()}_{hashlib.md5(url.encode('utf-8')).hexdigest()[:10]}"


def build_record(name, category, price, old_price, source, url):
    old_price = old_price if old_price and old_price > price else price
    return {
        "product_id": make_id(source, url),
        "name": name,
        "category": category,
        "current_price": price,
        "original_price": old_price,
        "discount_percent": round((1 - price / old_price) * 100, 1) if old_price > price else 0.0,
        "currency": "DH",
        "source": source,
        "url": url,
        "stock_status": "En Stock",
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }


class EcommerceScraper:
    def __init__(self, per_category: int = 10, delay: float = 1.0):
        self.per_category = per_category
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def _get(self, url: str):
        try:
            response = self.session.get(url, timeout=15)
        except requests.RequestException as exc:
            print(f"  request failed for {url}: {exc}")
            return None
        if response.status_code != 200:
            print(f"  HTTP {response.status_code} for {url} (site probably blocks scrapers)")
            return None
        return BeautifulSoup(response.content, "html.parser")

    def scrape_jumia(self, category: str, path: str) -> list:
        soup = self._get(f"https://www.jumia.ma/{path}")
        if soup is None:
            return []
        products = []
        for article in soup.select("article.prd")[: self.per_category]:
            link_el = article.find("a", class_="core")
            name_el = article.find("h3", class_="name") or article.find("div", class_="name")
            price_el = article.find("div", class_="prc")
            if not (link_el and name_el and price_el):
                continue
            price = parse_price(price_el.get_text())
            if price is None:
                continue
            old_el = article.find("div", class_="old")
            old_price = parse_price(old_el.get_text()) if old_el else parse_price(price_el.get("data-oprc", ""))
            href = link_el.get("href", "")
            url = f"https://www.jumia.ma{href}" if href.startswith("/") else href
            products.append(build_record(name_el.get_text(strip=True), category, price, old_price, "Jumia", url))
        return products

    def scrape_marjanemall(self, category: str, path: str) -> list:
        """MarjaneMall runs on Magento 2, so the standard product grid markup is used."""
        soup = self._get(f"https://www.marjanemall.ma/{path}")
        if soup is None:
            return []
        products = []
        for item in soup.select("li.product-item")[: self.per_category]:
            link_el = item.select_one("a.product-item-link")
            price_el = item.select_one("span.special-price span.price") or item.select_one("span.price")
            if not (link_el and price_el):
                continue
            price = parse_price(price_el.get_text())
            if price is None:
                continue
            old_el = item.select_one("span.old-price span.price")
            old_price = parse_price(old_el.get_text()) if old_el else None
            products.append(build_record(link_el.get_text(strip=True), category, price, old_price,
                                         "MarjaneMall", link_el.get("href", "")))
        return products

    def scrape_all(self) -> list:
        products = []
        for category, jumia_path, marjane_path in TARGETS:
            print(f"Scraping {category} ...")
            jumia = self.scrape_jumia(category, jumia_path)
            time.sleep(self.delay)
            marjane = self.scrape_marjanemall(category, marjane_path)
            time.sleep(self.delay)
            print(f"  Jumia: {len(jumia)} products, MarjaneMall: {len(marjane)} products")
            products.extend(jumia + marjane)
        return products


def load_sample() -> list:
    df = pd.read_csv(config.SAMPLE_FILE, dtype=str, keep_default_na=False)
    return df.to_dict(orient="records")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sample", action="store_true",
                        help="use the committed sample dataset instead of scraping the sites")
    parser.add_argument("--output", type=Path, default=config.BRONZE_FILE)
    parser.add_argument("--per-category", type=int, default=10)
    args = parser.parse_args(argv)

    if args.sample:
        products = load_sample()
        print(f"Sample mode: {len(products)} rows loaded from {config.SAMPLE_FILE}")
    else:
        products = EcommerceScraper(per_category=args.per_category).scrape_all()
        if not products:
            print("No product could be scraped (the sites are probably blocking requests). "
                  "Re-run with --sample to use the committed sample dataset.", file=sys.stderr)
            return 2

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as fh:
        json.dump(products, fh, ensure_ascii=False, indent=2)
    print(f"{len(products)} products written to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
