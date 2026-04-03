"""
SHEIN Singapore product scraper.

Scrapes fashion apparel from SHEIN SG and outputs
structured JSON matching the BuyWhere catalog schema for ingestion via
POST /v1/ingest/products.

Usage:
    python -m scrapers.shein_sg --api-key <key> [--batch-size 100] [--delay 1.0]
    python -m scrapers.shein_sg --scrape-only

Verticals covered:
- Women: Tops, Bottoms, Dresses, Jackets — target 20K
- Men: Tops, Bottoms, Jackets — target 15K
- Kids: Girls, Boys — target 8K
- Accessories: Bags, Jewelry, Hats — target 7K
- Total target: 50K products
"""
import argparse
import asyncio
import json
import os
import time
from typing import Any

import httpx

from scrapers.logging import get_logger

MERCHANT_ID = "shein_sg"
log = get_logger(MERCHANT_ID)
SOURCE = "shein_sg"
BASE_URL = "https://globering.shein.com"
OUTPUT_DIR = "/home/paperclip/buywhere-api/data/shein"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-SG,en;q=0.9",
    "Referer": "https://globering.shein.com/sg/",
    "X-Country": "sg",
    "X-Currency": "SGD",
}

CATEGORIES = [
    {"id": "women-tops", "name": "Women", "sub": "Tops", "url": "https://globering.shein.com/sg/women-tops-c--1577.html"},
    {"id": "women-bottoms", "name": "Women", "sub": "Bottoms", "url": "https://globering.shein.com/sg/women-bottoms-c-1578.html"},
    {"id": "women-dresses", "name": "Women", "sub": "Dresses", "url": "https://globering.shein.com/sg/women-dresses-c-1576.html"},
    {"id": "women-jackets", "name": "Women", "sub": "Jackets", "url": "https://globering.shein.com/sg/women-jackets-c-1579.html"},
    {"id": "men-tops", "name": "Men", "sub": "Tops", "url": "https://globering.shein.com/sg/men-tops-c-2609.html"},
    {"id": "men-bottoms", "name": "Men", "sub": "Bottoms", "url": "https://globering.shein.com/sg/men-bottoms-c-2610.html"},
    {"id": "men-jackets", "name": "Men", "sub": "Jackets", "url": "https://globering.shein.com/sg/men-jackets-c-2611.html"},
    {"id": "kids-girls", "name": "Kids", "sub": "Girls", "url": "https://globering.shein.com/sg/kids-girls-c-2947.html"},
    {"id": "kids-boys", "name": "Kids", "sub": "Boys", "url": "https://globering.shein.com/sg/kids-boys-c-2948.html"},
    {"id": "accessories-bags", "name": "Accessories", "sub": "Bags", "url": "https://globering.shein.com/sg/women-bags-c-1925.html"},
    {"id": "accessories-jewelry", "name": "Accessories", "sub": "Jewelry", "url": "https://globering.shein.com/sg/women-jewelry-c-10643.html"},
    {"id": "accessories-hats", "name": "Accessories", "sub": "Hats", "url": "https://globering.shein.com/sg/women-hats-c-10647.html"},
]


class SHEINScraper:
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
            except Exception:
                if attempt < retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    return None
        return None

    async def fetch_products_page(self, category: dict, page: int = 1) -> list[dict]:
        url = f"{BASE_URL}/share/product/search"
        params = {
            "page": page,
            "country": "SG",
            "currency": "SGD",
            "lang": "en",
            "category_id": category["id"],
            "sort": "1",
            "limit": 60,
        }
        try:
            data = await self._get_with_retry(url, params=params)
            if data:
                return data.get("products", []) or data.get("items", []) or data.get("result", {}).get("products", []) or []
            return []
        except Exception:
            return []

    def _extract_price(self, price_str: str | float | int) -> float:
        if isinstance(price_str, (int, float)):
            return float(price_str)
        cleaned = str(price_str).replace("$", "").replace(",", "").replace("SGD", "").strip()
        try:
            return float(cleaned)
        except ValueError:
            return 0.0

    def transform_product(self, raw: dict, category: dict) -> dict[str, Any] | None:
        try:
            sku = str(raw.get("goods_id", "") or raw.get("productId", "") or raw.get("id", ""))
            if not sku:
                return None

            title = raw.get("goods_name", "") or raw.get("title", "") or raw.get("productName", "")
            if not title:
                return None

            price = self._extract_price(raw.get("salePrice", raw.get("price", 0)))
            original_price = self._extract_price(
                raw.get("originalPrice", raw.get("shopPrice", raw.get("marketPrice", price)))
            )

            images = raw.get("imgs", []) or raw.get("images", []) or raw.get("image_url", [])
            image_url = ""
            if images:
                if isinstance(images[0], str):
                    image_url = images[0]
                elif isinstance(images[0], dict):
                    image_url = images[0].get("url", "") or images[0].get("src", "")

            product_url = raw.get("url", "") or raw.get("link", "") or raw.get("productUrl", "")
            if product_url and not product_url.startswith("http"):
                product_url = BASE_URL + product_url

            brand = raw.get("brand", "") or "SHEIN"

            rating = float(raw.get("rating", 0.0) or 0.0)
            review_count = int(raw.get("comment_count", raw.get("reviewCount", 0) or 0))

            discount = 0
            if original_price > price > 0:
                discount = int(((original_price - price) / original_price) * 100)

            color = raw.get("color", "") or ""
            size = raw.get("size", []) or raw.get("sizes", []) or []
            material = raw.get("material", "") or raw.get("composition", "")

            return {
                "sku": sku,
                "merchant_id": MERCHANT_ID,
                "title": title,
                "description": raw.get("description", "") or "",
                "price": price,
                "currency": "SGD",
                "url": product_url,
                "image_url": image_url,
                "category": category["name"],
                "category_path": [category["name"], category["sub"]],
                "brand": brand,
                "is_active": True,
                "metadata": {
                    "original_price": original_price,
                    "discount_pct": discount,
                    "rating": rating,
                    "review_count": review_count,
                    "subcategory": category["sub"],
                    "color": color,
                    "sizes": size,
                    "material": material,
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
        max_pages = 500

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
            batch = []

        self.total_scraped += counts["scraped"]
        print(f"  [{cat_name} / {sub_name}] Done: {counts}")
        return counts

    async def run(self) -> dict[str, Any]:
        mode = "scrape only" if self.scrape_only else f"API: {self.api_base}"
        print(f"SHEIN SG Scraper starting...")
        print(f"Mode: {mode}")
        print(f"Batch size: {self.batch_size}, Delay: {self.delay}s")
        print(f"Output: {self.products_outfile}")
        print(f"Categories: {len(CATEGORIES)} verticals")
        print(f"Verticals: Women, Men, Kids, Accessories")
        print(f"Target: 50K products")

        start = time.time()

        for cat in CATEGORIES:
            await self.scrape_category(cat)
            await asyncio.sleep(2)

        elapsed = time.time() - start

        summary = {
            "elapsed_seconds": round(elapsed, 1),
            "total_scraped": self.total_scraped,
            "total_ingested": self.total_ingested,
            "total_updated": self.total_updated,
            "total_failed": self.total_failed,
            "output_file": self.products_outfile,
        }

        print(f"\nScraper complete: {summary}")
        return summary


async def main():
    parser = argparse.ArgumentParser(description="SHEIN SG Scraper")
    parser.add_argument("--api-key", required=True, help="BuyWhere API key")
    parser.add_argument(
        "--api-base",
        default="http://localhost:8000",
        help="BuyWhere API base URL",
    )
    parser.add_argument("--batch-size", type=int, default=100)
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between batches (seconds)")
    parser.add_argument("--scrape-only", action="store_true", help="Save to JSONL without ingesting")
    args = parser.parse_args()

    scraper = SHEINScraper(
        api_key=args.api_key,
        api_base=args.api_base,
        batch_size=args.batch_size,
        delay=args.delay,
        scrape_only=args.scrape_only,
    )

    try:
        await scraper.run()
    finally:
        await scraper.close()


if __name__ == "__main__":
    asyncio.run(main())