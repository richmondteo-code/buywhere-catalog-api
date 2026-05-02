"""
Amazon Australia product scraper using ScraperAPI premium residential proxies.

Target: 500,000+ products across Electronics, Home, Fashion, Sports, Beauty.
Tag: region=au, country_code=AU, currency=AUD

Key features:
- ScraperAPI premium residential tier for anti-bot bypass
- Search-based scraping across keyword-driven categories
- Category path tagging for filtered catalog queries
- Deduplication by ASIN
- Concurrent scraping with per-category semaphore

Usage:
    SCRAPERAPI_KEY=... python -m scrapers.amazon_au --scrape-only --target 500000
    SCRAPERAPI_KEY=... python -m scrapers.amazon_au --api-key <key> --batch-size 200
"""

import argparse
import asyncio
import json
import os
import random
import re
import time
import urllib.parse
from typing import Any

import httpx
from bs4 import BeautifulSoup

MERCHANT_ID = "amazon_au"
SOURCE = "amazon_au"
BASE_URL = "https://www.amazon.com.au"
OUTPUT_DIR = "/home/paperclip/buywhere-api/data/amazon_au"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-AU,en;q=0.9",
    "Referer": "https://www.amazon.com.au/",
}

CATEGORIES = [
    {
        "id": "electronics",
        "name": "Electronics",
        "keywords": [
            "laptop",
            "smartphone",
            "headphones wireless",
            "4k monitor",
            "keyboard mechanical",
            "gaming mouse",
            "power bank",
            "smart watch",
            "tablet",
            "bluetooth speaker",
            "smart home hub",
            "webcam hd",
            "camera digital",
            "tv 55 inch",
            "soundbar",
        ],
    },
    {
        "id": "home",
        "name": "Home & Kitchen",
        "keywords": [
            "air fryer",
            "vacuum cleaner robot",
            "bedding set queen",
            "storage organiser",
            "desk lamp led",
            "cookware set nonstick",
            "office chair ergonomic",
            "water bottle stainless",
            "knife block set",
            "coffee maker machine",
            "air purifier HEPA",
            "mattress queen memory foam",
            "curtains blackout",
            "toaster oven",
            "blender high speed",
        ],
    },
    {
        "id": "fashion",
        "name": "Fashion",
        "keywords": [
            "women dress summer",
            "men shirt casual cotton",
            "running shoes women",
            "sneakers men",
            "handbag leather women",
            "wallet men leather",
            "hoodie pullover",
            "jacket winter women",
            "jeans women skinny",
            "athletic wear women",
            "socks pack cotton",
            "hat baseball cap",
            "scarf wool women",
            "sunglasses men UV",
            "watch men dress",
        ],
    },
    {
        "id": "beauty",
        "name": "Beauty & Personal Care",
        "keywords": [
            "skincare routine set",
            "makeup palette eyeshadow",
            "moisturiser face SPF",
            "shampoo hair loss",
            "electric toothbrush",
            "perfume women designer",
            "cologne men signature",
            "nail polish set",
            "hair dryer professional",
            "razor men electric",
            "lipstick long lasting",
            "serum vitamin C",
            "face mask sheet",
            "makeup brush set",
            "sunscreen SPF 50",
        ],
    },
    {
        "id": "sports",
        "name": "Sports & Outdoors",
        "keywords": [
            "fitness equipment home gym",
            "camping gear essentials",
            "hiking backpack 40L",
            "cycling helmet adult",
            "yoga mat premium thick",
            "dumbbells set 20kg",
            "fishing rod combo",
            "running shoes men trail",
            "sports jersey football",
            "outdoor recreation equipment",
            "winter sports gear",
            "team sports ball soccer",
            "sports accessories fitness",
            "kettlebell cast iron",
            "exercise bike magnetic",
        ],
    },
    {
        "id": "toys",
        "name": "Toys & Games",
        "keywords": [
            "lego city set",
            "barbie doll fashion",
            "action figure marvel",
            "board game family",
            "puzzle 1000 pieces",
            "outdoor toy kids",
            "educational toy age 5",
            "remote control car 4wd",
            "building blocks creative",
            "dollhouse wooden",
            "arts crafts kit kids",
            "nerf gun elite",
            "video game console ps5",
            "toy train set",
            "dinosaur action figure",
        ],
    },
    {
        "id": "books",
        "name": "Books",
        "keywords": [
            "bestseller fiction 2024",
            "self help book",
            "cookbook australian",
            "biography famous",
            "science fiction book",
            "mystery novel thriller",
            "business book leadership",
            "children books age 6",
            "audiobook bestseller",
            "journal refill lined",
            "colouring book adult",
            "puzzle book crosswords",
            "fantasy novel 2024",
            "romance book bestseller",
            "travel guide australia",
        ],
    },
    {
        "id": "grocery",
        "name": "Grocery & Gourmet",
        "keywords": [
            "organic coffee beans",
            "protein powder",
            "healthy snack boxes",
            "olive oil extra virgin",
            "tea loose leaf",
            "chocolate block dark",
            "nuts mixed raw",
            "pasta dried italian",
            "sauce pasta tomato",
            "spice rack set",
            "honey manuka",
            "milk oat organic",
            "bread sourdough",
            "cereal granola",
            "rice basmati long grain",
        ],
    },
]


class AmazonAUScraper:
    def __init__(
        self,
        scrape_only: bool = True,
        target: int = 500000,
        delay: float = 1.5,
        concurrency: int = 8,
        max_pages_per_keyword: int = 50,
        scraperapi_key: str | None = None,
        batch_size: int = 100,
        api_base: str = "http://localhost:8000",
        api_key: str | None = None,
    ):
        self.scrape_only = scrape_only
        self.target = target
        self.delay = delay
        self.concurrency = concurrency
        self.max_pages_per_keyword = max_pages_per_keyword
        self.scraperapi_key = scraperapi_key or os.environ.get("SCRAPERAPI_KEY", "")
        self.batch_size = batch_size
        self.api_base = api_base.rstrip("/")
        self.api_key = api_key or os.environ.get("BUYWHERE_API_KEY")
        self._semaphore = asyncio.Semaphore(concurrency)
        self._client = httpx.AsyncClient(timeout=120.0, headers=HEADERS)
        self._seen_asins: set[str] = set()
        self._all_seen_skus: set[str] = set()
        self.total_scraped = 0
        self.total_ingested = 0
        self.total_updated = 0
        self.total_failed = 0
        self._ensure_output_dir()
        ts = time.strftime("%Y%m%d_%H%M%S")
        self._output_file = os.path.join(OUTPUT_DIR, f"amazon_au_{ts}.ndjson")
        self._skipped_file = os.path.join(OUTPUT_DIR, f"amazon_au_skipped_{ts}.txt")

    def _ensure_output_dir(self) -> None:
        os.makedirs(OUTPUT_DIR, exist_ok=True)

    async def close(self) -> None:
        await self._client.aclose()

    async def _fetch_with_scraperapi(
        self, url: str, retries: int = 3, autoparse: bool = False
    ) -> str | None:
        encoded_url = urllib.parse.quote(url, safe="")
        flags = "&autoparse=true" if autoparse else "&premium=true&keep_headers=true"
        proxy_url = (
            f"http://api.scraperapi.com?api_key={self.scraperapi_key}&url={encoded_url}"
            f"{flags}"
        )
        await asyncio.sleep(random.uniform(0.5, 2.0))
        for attempt in range(retries):
            try:
                resp = await self._client.get(proxy_url, timeout=120.0)
                text = resp.text
                if resp.status_code == 200 and len(text) > 1000:
                    if "captcha" in text.lower() or "robot check" in text.lower():
                        print(f"  CAPTCHA/robot check for {url}, retry {attempt+1}/{retries}")
                        await asyncio.sleep(15 * (attempt + 1))
                        continue
                    return text
                elif resp.status_code in (500, 429, 503):
                    wait_time = (2 ** attempt) * 10
                    print(f"  HTTP {resp.status_code}, waiting {wait_time}s")
                    await asyncio.sleep(wait_time)
                    continue
            except Exception as e:
                print(f"  Exception fetching {url}: {e}")
                await asyncio.sleep(2 ** attempt)
                continue
        return None

    def _parse_autoparse_results(
        self, raw_text: str
    ) -> tuple[list[dict[str, Any]], int]:
        try:
            data = json.loads(raw_text)
            items = data.get("results", []) if isinstance(data, dict) else []
        except Exception:
            return [], 0

        products: list[dict[str, Any]] = []
        for item in items:
            if item.get("type") != "search_product":
                continue
            try:
                asin = item.get("asin", "")
                if not asin or asin in self._seen_asins:
                    continue

                price_info = item.get("price", {}) or {}
                price_val = price_info.get("value", 0) if isinstance(price_info, dict) else 0
                orig_info = item.get("original_price") or {}
                orig_val = (
                    orig_info.get("value", price_val)
                    if isinstance(orig_info, dict)
                    else price_val
                )

                rating_info = item.get("rating", {}) or {}
                rating = rating_info.get("value", 0) if isinstance(rating_info, dict) else 0
                review_count = rating_info.get("total_reviews", 0) if isinstance(rating_info, dict) else 0

                url = item.get("url", "") or f"{BASE_URL}/dp/{asin}"
                if not url.startswith("http"):
                    url = urllib.parse.urljoin(BASE_URL, url)

                raw_product = {
                    "asin": asin,
                    "title": item.get("name", ""),
                    "url": url,
                    "price": price_val,
                    "original_price": orig_val,
                    "image_url": item.get("thumbnail", ""),
                    "rating": rating,
                    "review_count": review_count,
                    "is_sponsored": bool(item.get("is_sponsored")),
                }
                transformed = self.transform_product(raw_product, "", "")
                if transformed:
                    products.append(transformed)
            except Exception:
                continue

        next_page = data.get("next_page", 0) if isinstance(data, dict) else 0
        return products, next_page

    def _write_products(self, products: list[dict]) -> None:
        if not products:
            return
        with open(self._output_file, "a", encoding="utf-8") as f:
            for p in products:
                sku = p.get("sku", "")
                if sku:
                    self._all_seen_skus.add(sku)
                f.write(json.dumps(p, ensure_ascii=False) + "\n")

    def _log_skipped(self, asin: str, reason: str) -> None:
        with open(self._skipped_file, "a", encoding="utf-8") as f:
            f.write(f"{asin}: {reason}\n")

    def _parse_price(self, value: str | None) -> float:
        if not value:
            return 0.0
        cleaned = value.replace("A$", "").replace("$", "").replace("£", "").replace(",", "").strip()
        match = re.search(r"\d+(?:\.\d+)?", cleaned)
        return float(match.group(0)) if match else 0.0

    def _parse_int(self, value: str | None) -> int:
        if not value:
            return 0
        digits = re.sub(r"[^\d]", "", value)
        return int(digits) if digits else 0

    def _extract_brand(self, title: str) -> str:
        if not title:
            return ""
        first_token = title.split()[0].strip("()-[]:,.")
        if not first_token or any(c.isdigit() for c in first_token):
            return ""
        return first_token[:80]

    def parse_search_results(
        self, html: str, category_name: str, keyword: str
    ) -> tuple[list[dict[str, Any]], bool]:
        soup = BeautifulSoup(html, "html.parser")
        products: list[dict[str, Any]] = []

        for card in soup.select('[data-component-type="s-search-result"][data-asin]'):
            asin = (card.get("data-asin") or "").strip()
            if not asin:
                continue

            title_el = card.select_one("h2 span")
            if not title_el:
                continue

            link_el = card.select_one("h2 a")
            price_el = card.select_one(".a-price .a-offscreen")
            original_price_el = card.select_one(".a-text-price .a-offscreen")
            image_el = card.select_one("img.s-image")
            rating_el = card.select_one(".a-icon-alt")
            review_el = card.select_one('a[href*="#customerReviews"] span')
            sponsored_el = card.select_one(
                '[aria-label="Sponsored"], .puis-sponsored-label-text'
            )

            raw_product = {
                "asin": asin,
                "title": title_el.get_text(" ", strip=True),
                "url": link_el.get("href", "") if link_el else "",
                "price": price_el.get_text(strip=True) if price_el else "",
                "original_price": (
                    original_price_el.get_text(strip=True)
                    if original_price_el
                    else ""
                ),
                "image_url": image_el.get("src", "") if image_el else "",
                "rating": rating_el.get_text(" ", strip=True) if rating_el else "",
                "review_count": (
                    review_el.get_text(" ", strip=True) if review_el else ""
                ),
                "is_sponsored": sponsored_el is not None,
            }

            transformed = self.transform_product(
                raw_product, category_name, keyword
            )
            if transformed:
                products.append(transformed)

        next_btn = soup.select_one(".s-pagination-next:not(.s-pagination-disabled)")
        has_next_page = next_btn is not None
        return products, has_next_page

    def transform_product(
        self, raw: dict[str, Any], category_name: str, keyword: str
    ) -> dict[str, Any] | None:
        try:
            asin = str(raw.get("asin", "") or raw.get("sku", "")).strip()
            if not asin or asin in self._seen_asins:
                return None
            self._seen_asins.add(asin)

            title = (raw.get("title") or "").strip()
            if not title:
                return None

            url = raw.get("url") or f"{BASE_URL}/dp/{asin}"
            if not url.startswith("http"):
                url = urllib.parse.urljoin(BASE_URL, url)

            price = self._parse_price(raw.get("price"))
            original_price = (
                self._parse_price(raw.get("original_price")) or price
            )
            review_count = self._parse_int(raw.get("review_count"))

            rating = 0.0
            rating_text = raw.get("rating") or ""
            rating_match = re.search(r"(\d+(?:\.\d+)?)", rating_text)
            if rating_match:
                rating = float(rating_match.group(1))

            category_path = [category_name]
            if keyword and keyword.lower() != category_name.lower():
                category_path.append(keyword)

            return {
                "sku": asin,
                "merchant_id": MERCHANT_ID,
                "title": title,
                "description": raw.get("description") or "",
                "price": price,
                "currency": "AUD",
                "url": url,
                "image_url": raw.get("image_url") or "",
                "category": category_name,
                "category_path": category_path,
                "brand": raw.get("brand") or self._extract_brand(title),
                "is_active": True,
                "metadata": {
                    "keyword": keyword,
                    "original_price": original_price,
                    "rating": rating,
                    "review_count": review_count,
                    "is_sponsored": bool(raw.get("is_sponsored", False)),
                    "region": "au",
                    "country_code": "AU",
                    "source_type": "scraperapi_premium_residential",
                    "scraped_at": int(time.time()),
                    "amazon_asin": asin,
                },
            }
        except Exception:
            return None

    async def fetch_search_page(
        self, keyword: str, page: int = 1
    ) -> tuple[list[dict[str, Any]], bool]:
        query_params = f"k={urllib.parse.quote(keyword, safe='')}&page={page}"
        url = f"{BASE_URL}/s?{query_params}"
        raw = await self._fetch_with_scraperapi(url, autoparse=True)
        if not raw:
            return [], False
        products, next_page = self._parse_autoparse_results(raw)
        has_next_page = bool(next_page)
        return products, has_next_page

    async def _ingest_batch(
        self, products: list[dict[str, Any]]
    ) -> tuple[int, int, int]:
        if not products:
            return 0, 0, 0
        if self.scrape_only:
            self._write_products(products)
            return len(products), 0, 0

        url = f"{self.api_base}/v1/ingest/products"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {"source": SOURCE, "products": products}

        try:
            resp = await self._client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            result = resp.json()
            return (
                result.get("rows_inserted", 0),
                result.get("rows_updated", 0),
                result.get("rows_failed", 0),
            )
        except Exception as e:
            print(f"  Ingestion error: {e}")
            return 0, 0, len(products)

    async def scrape_keyword(
        self, category: dict[str, Any], keyword: str
    ) -> dict[str, int]:
        category_name = category["name"]
        print(f"\n[{category_name}] keyword='{keyword}'")
        counts: dict[str, int] = {
            "scraped": 0,
            "ingested": 0,
            "updated": 0,
            "failed": 0,
        }
        batch: list[dict[str, Any]] = []

        for page in range(1, self.max_pages_per_keyword + 1):
            if self.target > 0 and self.total_scraped >= self.target:
                break

            async with self._semaphore:
                parsed_products, has_next_page = await self.fetch_search_page(
                    keyword, page
                )

            if not parsed_products:
                print(f"  Page {page}: no products")
                if not has_next_page:
                    break
                await asyncio.sleep(self.delay)
                continue

            for product in parsed_products:
                asin = product.get("sku", "")
                if asin in self._seen_asins:
                    continue
                self._seen_asins.add(asin)
                batch.append(product)
                counts["scraped"] += 1

                if len(batch) >= self.batch_size:
                    i, u, f = await self._ingest_batch(batch)
                    counts["ingested"] += i
                    counts["updated"] += u
                    counts["failed"] += f
                    self.total_ingested += i
                    self.total_updated += u
                    self.total_failed += f
                    self.total_scraped += i
                    batch = []
                    await asyncio.sleep(self.delay)

            print(
                f"  Page {page}: parsed={len(parsed_products)} new={counts['scraped']} "
                f"total={self.total_scraped}"
            )

            if not has_next_page:
                break

            await asyncio.sleep(self.delay)

        if batch:
            i, u, f = await self._ingest_batch(batch)
            counts["ingested"] += i
            counts["updated"] += u
            counts["failed"] += f
            self.total_ingested += i
            self.total_updated += u
            self.total_failed += f
            self.total_scraped += i

        return counts

    async def run(self) -> dict[str, Any]:
        print("Amazon AU Scraper starting...")
        print(f"Target: {self.target} products")
        print(f"Mode: {'scrape only' if self.scrape_only else f'API: {self.api_base}'}")
        print(f"Output file: {self._output_file}")
        print(f"Categories: {len(CATEGORIES)}")
        print(f"Concurrency: {self.concurrency}")

        start = time.time()

        tasks = [
            self.scrape_keyword(cat, kw)
            for cat in CATEGORIES
            for kw in cat["keywords"]
        ]
        results = await asyncio.gather(*tasks)

        elapsed = time.time() - start

        total_scraped = sum(r.get("scraped", 0) for r in results)
        total_ingested = sum(r.get("ingested", 0) for r in results)
        total_updated = sum(r.get("updated", 0) for r in results)
        total_failed = sum(r.get("failed", 0) for r in results)

        summary = {
            "elapsed_seconds": round(elapsed, 1),
            "total_scraped": total_scraped,
            "total_ingested": total_ingested,
            "total_updated": total_updated,
            "total_failed": total_failed,
            "unique_asins": len(self._seen_asins),
            "output_file": self._output_file,
            "categories_covered": len(CATEGORIES),
        }
        print(f"Scraper complete: {summary}")
        return summary


async def main() -> None:
    parser = argparse.ArgumentParser(description="Amazon.com.au Australia product scraper")
    parser.add_argument(
        "--scrape-only",
        action="store_true",
        default=True,
        help="Save to NDJSON without ingesting",
    )
    parser.add_argument(
        "--target",
        type=int,
        default=500000,
        help="Target number of products (0 = unlimited)",
    )
    parser.add_argument(
        "--delay", type=float, default=1.5, help="Delay between requests (seconds)"
    )
    parser.add_argument(
        "--concurrency", type=int, default=8, help="Max concurrent keyword scrapes"
    )
    parser.add_argument(
        "--max-pages-per-keyword",
        type=int,
        default=50,
        help="Max pages per keyword",
    )
    parser.add_argument(
        "--scraperapi-key", default=None, help="ScraperAPI key (or env SCRAPERAPI_KEY)"
    )
    parser.add_argument(
        "--api-key", default=None, help="BuyWhere API key (for ingestion)"
    )
    parser.add_argument(
        "--api-base",
        default="http://localhost:8000",
        help="BuyWhere API base URL",
    )
    parser.add_argument(
        "--batch-size", type=int, default=100, help="Batch size for ingestion"
    )
    args = parser.parse_args()

    scraper = AmazonAUScraper(
        scrape_only=args.scrape_only,
        target=args.target,
        delay=args.delay,
        concurrency=args.concurrency,
        max_pages_per_keyword=args.max_pages_per_keyword,
        scraperapi_key=args.scraperapi_key,
        batch_size=args.batch_size,
        api_base=args.api_base,
        api_key=args.api_key,
    )
    try:
        await scraper.run()
    finally:
        await scraper.close()


if __name__ == "__main__":
    asyncio.run(main())
