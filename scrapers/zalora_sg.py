"""
Zalora Singapore fashion product scraper.

Scrapes fashion apparel from Zalora SG across men, women, kids, beauty,
and sports categories, outputting structured JSON matching the BuyWhere
catalog schema for ingestion via POST /v1/ingest/products.

Usage:
    python -m scrapers.zalora_sg --api-key <key> [--batch-size 100] [--delay 1.0]
    python -m scrapers.zalora_sg --scrape-only

Verticals covered:
- Women: Dresses, Tops, Bottoms, Jackets — target 15K
- Men: Tops, Bottoms, Jackets — target 12K
- Kids: Girls, Boys — target 8K
- Beauty: Skincare, Makeup, Fragrances — target 8K
- Sports: Activewear, Footwear — target 7K
- Total target: 50K products
"""
import argparse
import asyncio
import json
import os
import re
import time
from typing import Any

import httpx

from scrapers.logging import get_logger

MERCHANT_ID = "zalora_sg"
log = get_logger(MERCHANT_ID)
SOURCE = "zalora_sg"
BASE_URL = "https://www.zalora.sg"
OUTPUT_DIR = "/home/paperclip/buywhere-api/data/zalora"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-SG,en;q=0.9",
    "Referer": "https://www.zalora.sg/",
    "X-Requested-With": "XMLHttpRequest",
}

CATEGORIES = [
    {"id": "women-dresses", "name": "Women", "sub": "Dresses", "url": "https://www.zalora.sg/dresses/"},
    {"id": "women-tops", "name": "Women", "sub": "Tops", "url": "https://www.zalora.sg/women-tops/"},
    {"id": "women-bottoms", "name": "Women", "sub": "Bottoms", "url": "https://www.zalora.sg/women-pants-leggings/"},
    {"id": "women-jackets", "name": "Women", "sub": "Jackets", "url": "https://www.zalora.sg/women-jackets-coats/"},
    {"id": "men-tops", "name": "Men", "sub": "Tops", "url": "https://www.zalora.sg/men-tshirts/"},
    {"id": "men-bottoms", "name": "Men", "sub": "Bottoms", "url": "https://www.zalora.sg/men-pants/"},
    {"id": "men-jackets", "name": "Men", "sub": "Jackets", "url": "https://www.zalora.sg/men-jackets/"},
    {"id": "kids-girls", "name": "Kids", "sub": "Girls", "url": "https://www.zalora.sg/girls/"},
    {"id": "kids-boys", "name": "Kids", "sub": "Boys", "url": "https://www.zalora.sg/boys/"},
    {"id": "beauty-skincare", "name": "Beauty", "sub": "Skincare", "url": "https://www.zalora.sg/skincare/"},
    {"id": "beauty-makeup", "name": "Beauty", "sub": "Makeup", "url": "https://www.zalora.sg/makeup/"},
    {"id": "beauty-fragrances", "name": "Beauty", "sub": "Fragrances", "url": "https://www.zalora.sg/fragrances/"},
    {"id": "sports-activewear", "name": "Sports", "sub": "Activewear", "url": "https://www.zalora.sg/sportswear/"},
    {"id": "sports-footwear", "name": "Sports", "sub": "Footwear", "url": "https://www.zalora.sg/shoes/"},
]


class ZaloraScraper:
    def __init__(
        self,
        api_key: str,
        api_base: str = "http://localhost:8000",
        batch_size: int = 100,
        delay: float = 1.0,
        scrape_only: bool = False,
    ):
        self.api_key = api_key
        self.api_base = api_base.rstrip("/")
        self.batch_size = batch_size
        self.delay = delay
        self.scrape_only = scrape_only
        self.client = httpx.AsyncClient(timeout=30.0, headers=HEADERS)
        self.total_scraped = 0
        self.total_ingested = 0
        self.total_updated = 0
        self.total_failed = 0
        self.products_outfile = None
        self._ensure_output_dir()

    def _ensure_output_dir(self):
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        ts = time.strftime("%Y%m%d_%H%M%S")
        self.products_outfile = os.path.join(OUTPUT_DIR, f"products_{ts}.jsonl")

    async def close(self):
        await self.client.aclose()

    async def _get_with_retry(
        self, url: str, params: dict | None = None, retries: int = 3
    ) -> dict[str, Any] | None:
        for attempt in range(retries):
            try:
                resp = await self.client.get(url, params=params)
                resp.raise_for_status()
                return resp.json()
            except Exception as e:
                log.request_failed(url, attempt, str(e))
                if attempt < retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    return None
        return None

    def _extract_price(self, price_str: str | float | int) -> float:
        if isinstance(price_str, (int, float)):
            return float(price_str)
        cleaned = str(price_str).replace("$", "").replace(",", "").replace("SGD", "").strip()
        try:
            return float(cleaned)
        except ValueError:
            return 0.0

    async def fetch_products_page(self, category: dict, page: int = 1) -> list[dict]:
        url = f"{BASE_URL}/_c/v1/desktop/list_product_l2"
        params = {
            "category": category["id"],
            "page": page,
            "page_size": 60,
            "sort": "popularity",
            "filter": "popularity",
            "q": "",
            "b": "1",
        }
        try:
            data = await self._get_with_retry(url, params=params)
            if data:
                products = data.get("data", {}).get("products", []) or data.get("products", []) or []
                return products
            return []
        except Exception:
            return []

    def transform_product(self, raw: dict, category: dict) -> dict[str, Any] | None:
        try:
            sku = str(raw.get("sku", "") or raw.get("product_id", "") or raw.get("id", ""))
            if not sku:
                return None

            title = raw.get("name", "") or raw.get("product_name", "") or raw.get("title", "")
            if not title:
                return None

            price_data = raw.get("price", {}) or raw
            if isinstance(price_data, str):
                price = self._extract_price(price_data)
                original_price = price
            else:
                price = self._extract_price(price_data.get("current", price_data.get("price", 0)))
                original_price = self._extract_price(
                    price_data.get("original", price_data.get("original_price", price_data.get("was_price", price)))
                )

            discount = 0
            if original_price > price > 0:
                discount = round(((original_price - price) / original_price) * 100)

            brand = raw.get("brand_name", "") or raw.get("brand", "") or ""

            image_urls = []
            raw_images = raw.get("media", {}).get("images", []) or raw.get("images", []) or raw.get("gallery", []) or []
            for img in raw_images:
                if isinstance(img, str):
                    image_urls.append(img)
                elif isinstance(img, dict):
                    url = img.get("url", "") or img.get("src", "") or img.get("large", "") or img.get("small", "")
                    if url:
                        image_urls.append(url)

            image_url = image_urls[0] if image_urls else ""

            rating = raw.get("rating", {}).get("average", 0.0) if isinstance(raw.get("rating"), dict) else raw.get("rating", 0.0) or 0.0
            review_count = raw.get("rating", {}).get("count", 0) if isinstance(raw.get("rating"), dict) else raw.get("review_count", 0) or 0

            raw_sizes = raw.get("size", []) or raw.get("sizes", []) or raw.get("available_sizes", []) or []
            sizes = []
            for s in raw_sizes:
                if isinstance(s, str):
                    sizes.append(s)
                elif isinstance(s, dict):
                    size_name = s.get("name", "") or s.get("label", "") or s.get("value", "")
                    if size_name:
                        sizes.append(size_name)

            raw_colors = raw.get("color", []) or raw.get("colors", []) or raw.get("variants", []) or []
            colors = []
            for c in raw_colors:
                if isinstance(c, str):
                    colors.append(c)
                elif isinstance(c, dict):
                    color_name = c.get("name", "") or c.get("label", "") or c.get("value", "")
                    if color_name:
                        colors.append(color_name)

            product_url = raw.get("url", "") or raw.get("link", "") or ""
            if product_url and not product_url.startswith("http"):
                product_url = BASE_URL + product_url

            category_path = raw.get("category_path", []) or [category["name"], category["sub"]]

            return {
                "sku": sku,
                "merchant_id": MERCHANT_ID,
                "title": title,
                "description": "",
                "price": price,
                "currency": "SGD",
                "url": product_url,
                "image_url": image_url,
                "category": category["name"],
                "category_path": category_path,
                "brand": brand,
                "is_active": True,
                "metadata": {
                    "original_price": original_price,
                    "discount_pct": discount,
                    "rating": rating,
                    "review_count": review_count,
                    "sizes": sizes,
                    "colors": colors,
                    "images": image_urls,
                },
            }
        except Exception:
            return None

    def _write_products_to_file(self, products: list[dict]):
        if not products:
            return
        with open(self.products_outfile, "a", encoding="utf-8") as f:
            for p in products:
                f.write(json.dumps(p, ensure_ascii=False) + "\n")

    async def ingest_batch(self, products: list[dict]) -> tuple[int, int, int]:
        if not products:
            return 0, 0, 0

        if self.scrape_only:
            self._write_products_to_file(products)
            return len(products), 0, 0

        url = f"{self.api_base}/v1/ingest/products"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {"source": SOURCE, "products": products}

        try:
            resp = await self.client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            result = resp.json()
            return (
                result.get("rows_inserted", 0),
                result.get("rows_updated", 0),
                result.get("rows_failed", 0),
            )
        except Exception as e:
            log.ingestion_error(None, str(e))
            return 0, 0, len(products)

    async def scrape_category(self, category: dict) -> dict[str, int]:
        cat_id = category["id"]
        cat_name = category["name"]
        sub_name = category["sub"]

        print(f"\n[{cat_name} / {sub_name}] Starting scrape...")
        counts = {"scraped": 0, "ingested": 0, "updated": 0, "failed": 0}
        page = 1
        batch = []
        consecutive_empty = 0
        max_pages = 5000

        while consecutive_empty < 5 and page <= max_pages:
            print(f"  Page {page}...", end=" ", flush=True)
            products = await self.fetch_products_page(category, page)

            if not products:
                consecutive_empty += 1
                print("No products found.")
                if consecutive_empty >= 3:
                    break
                page += 1
                await asyncio.sleep(self.delay)
                continue

            consecutive_empty = 0

            for raw in products:
                transformed = self.transform_product(raw, category)
                if transformed:
                    batch.append(transformed)
                    counts["scraped"] += 1

                    if len(batch) >= self.batch_size:
                        i, u, f = await self.ingest_batch(batch)
                        counts["ingested"] += i
                        counts["updated"] += u
                        counts["failed"] += f
                        self.total_ingested += i
                        self.total_updated += u
                        self.total_failed += f
                        batch = []
                        await asyncio.sleep(self.delay)

            print(f"scraped={counts['scraped']}")

            if len(products) < 60:
                break

            page += 1
            await asyncio.sleep(self.delay)

        if batch:
            i, u, f = await self.ingest_batch(batch)
            counts["ingested"] += i
            counts["updated"] += u
            counts["failed"] += f
            self.total_ingested += i
            self.total_updated += u
            self.total_failed += f

        print(f"  [{cat_name} / {sub_name}] Done: scraped={counts['scraped']}, ingested={counts['ingested']}, updated={counts['updated']}, failed={counts['failed']}")
        return counts

    async def run(self):
        print(f"Zalora SG Scraper starting — target: 50K products")
        print(f"API: {self.api_base} | Batch: {self.batch_size} | Delay: {self.delay}s")
        print(f"Scrape only: {self.scrape_only}")

        overall = {"scraped": 0, "ingested": 0, "updated": 0, "failed": 0}

        for category in CATEGORIES:
            try:
                counts = await self.scrape_category(category)
                overall["scraped"] += counts["scraped"]
                overall["ingested"] += counts["ingested"]
                overall["updated"] += counts["updated"]
                overall["failed"] += counts["failed"]
            except Exception as e:
                log.parse_error(None, f"Category scrape failed: {e}")

        print(f"\n=== Overall ===")
        print(f"Scraped: {overall['scraped']}")
        print(f"Ingested: {overall['ingested']}")
        print(f"Updated: {overall['updated']}")
        print(f"Failed: {overall['failed']}")
        if not self.scrape_only:
            print(f"Total ingested (all batches): {self.total_ingested}")
            print(f"Total updated (all batches): {self.total_updated}")
            print(f"Total failed (all batches): {self.total_failed}")

        await self.close()


def main():
    parser = argparse.ArgumentParser(description="Zalora SG product scraper")
    parser.add_argument("--api-key", required=True, help="BuyWhere API key")
    parser.add_argument("--api-base", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for ingestion")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between requests (seconds)")
    parser.add_argument("--scrape-only", action="store_true", help="Save to file instead of ingesting")
    args = parser.parse_args()

    scraper = ZaloraScraper(
        api_key=args.api_key,
        api_base=args.api_base,
        batch_size=args.batch_size,
        delay=args.delay,
        scrape_only=args.scrape_only,
    )
    asyncio.run(scraper.run())


if __name__ == "__main__":
    main()