"""
SHEIN Singapore product scraper.

Current implementation tracks the live SG site structure, discovers category
seeds from the homepage, and writes normalized output to the path requested by
BUY-1649.

Usage:
    python3 -m scrapers.shein_sg --api-key <key>
    python3 -m scrapers.shein_sg --scrape-only
    python3 -m scrapers.shein_sg --discover-only
"""

import argparse
import asyncio
import json
import os
import re
import time
from typing import Any
from urllib.parse import unquote, urljoin

import cloudscraper
import httpx

from scrapers.scraper_logging import get_logger

MERCHANT_ID = "shein_sg"
SOURCE = "shein_sg"
BASE_URL = "https://sg.shein.com"
HOME_URL = f"{BASE_URL}/sg-en/"
LIST_API_URL = f"{BASE_URL}/category/real_category_goods_list"
NORMALIZED_OUTPUT_DIR = "/home/paperclip/buywhere-api/data/normalized"
NORMALIZED_OUTPUT_FILE = os.path.join(
    NORMALIZED_OUTPUT_DIR, "shein_sg_normalized.ndjson"
)

HTML_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-SG,en;q=0.9",
    "Referer": HOME_URL,
}

API_HEADERS = {
    **HTML_HEADERS,
    "Accept": "application/json, text/plain, */*",
    "X-Requested-With": "XMLHttpRequest",
}

STATIC_CATEGORIES = [
    {
        "id": "men-shirt-coords",
        "cat_id": "9037",
        "name": "Men",
        "sub": "Shirt Co-ords",
        "url": f"{BASE_URL}/Men-Shirt-Co-ords-c-9037.html",
    }
]

FASHION_KEYWORDS = (
    "women",
    "men",
    "kids",
    "girls",
    "boys",
    "curve",
    "plus",
    "shoe",
    "bag",
    "dress",
    "tops",
    "bottom",
    "jacket",
    "denim",
    "activewear",
    "accessories",
    "fashion",
)

RISK_MARKERS = (
    "/risk/challenge",
    "captcha_type=",
    "risk-id=",
    "irregular activities",
    "risk challenge",
)

log = get_logger(MERCHANT_ID)


class SheinRiskChallengeError(RuntimeError):
    """Raised when SHEIN returns a challenge page or blocked listing response."""


class SHEINScraper:
    def __init__(
        self,
        api_key: str,
        api_base: str = "http://localhost:8000",
        batch_size: int = 100,
        delay: float = 1.0,
        scrape_only: bool = False,
        discover_only: bool = False,
    ):
        self.api_key = api_key
        self.api_base = api_base.rstrip("/")
        self.batch_size = batch_size
        self.delay = delay
        self.scrape_only = scrape_only
        self.discover_only = discover_only
        self.cf_scraper = cloudscraper.create_scraper(
            browser={"browser": "chrome", "platform": "windows", "mobile": False}
        )
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self.total_scraped = 0
        self.total_ingested = 0
        self.total_updated = 0
        self.total_failed = 0
        self.challenge_detected = False
        self.products_outfile = NORMALIZED_OUTPUT_FILE
        self._ensure_output_dir()

    def _ensure_output_dir(self) -> None:
        os.makedirs(NORMALIZED_OUTPUT_DIR, exist_ok=True)
        if self.scrape_only:
            with open(self.products_outfile, "w", encoding="utf-8"):
                pass

    async def close(self) -> None:
        self.cf_scraper.close()
        await self.http_client.aclose()

    @staticmethod
    def _is_risk_challenge(url: str, text: str) -> bool:
        lowered = f"{url}\n{text[:5000]}".lower()
        return any(marker in lowered for marker in RISK_MARKERS)

    @staticmethod
    def _normalize_category_seed(
        cat_id: str, category_name: str, relative_url: str
    ) -> dict[str, str] | None:
        slug = relative_url.split("/")[-1].split(".html")[0]
        slug_words = slug.replace("-c-", "-").split("-")
        text = " ".join(filter(None, [category_name, slug])).lower()
        if not any(keyword in text for keyword in FASHION_KEYWORDS):
            return None

        if "women" in text or "lady" in text or "curve" in text:
            top = "Women"
        elif "men" in text:
            top = "Men"
        elif "kid" in text or "girl" in text or "boy" in text:
            top = "Kids"
        elif "shoe" in text:
            top = "Shoes"
        elif "bag" in text or "accessor" in text:
            top = "Accessories"
        else:
            top = "Fashion"

        sub_parts = [
            word
            for word in slug_words
            if word
            and word.lower() not in {"c", cat_id.lower(), top.lower(), "sg", "en"}
            and not word.isdigit()
        ]
        sub = " ".join(word.capitalize() for word in sub_parts[:4]) or category_name
        return {
            "id": slug,
            "cat_id": cat_id,
            "name": top,
            "sub": sub,
            "url": urljoin(BASE_URL, relative_url),
        }

    @classmethod
    def extract_categories_from_homepage(cls, html: str) -> list[dict[str, str]]:
        pattern = re.compile(
            r'"webClickUrl":"(?P<url>(?:\\/|/)[^"]+-c-(?P<cat_id>\d+)\.html)".{0,300}?"categoryName":"(?P<name>[^"]+)"',
            re.DOTALL,
        )
        categories: list[dict[str, str]] = []
        seen: set[str] = set()
        for match in pattern.finditer(html):
            relative_url = unquote(match.group("url")).replace("\\/", "/")
            category = cls._normalize_category_seed(
                match.group("cat_id"),
                match.group("name"),
                relative_url,
            )
            if not category:
                continue
            key = f'{category["cat_id"]}:{category["url"]}'
            if key in seen:
                continue
            seen.add(key)
            categories.append(category)
        return categories

    async def _fetch_html(self, url: str, retries: int = 3) -> str:
        for attempt in range(retries):
            try:
                loop = asyncio.get_running_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: self.cf_scraper.get(url, headers=HTML_HEADERS, timeout=30),
                )
                text = response.text or ""
                final_url = getattr(response, "url", url)
                if self._is_risk_challenge(str(final_url), text):
                    raise SheinRiskChallengeError(
                        f"Risk challenge on {final_url} while fetching {url}"
                    )
                if response.status_code >= 400 and "<html" not in text.lower():
                    response.raise_for_status()
                return text
            except SheinRiskChallengeError:
                self.challenge_detected = True
                raise
            except Exception as exc:
                log.request_failed(url, attempt, str(exc))
                if attempt == retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)
        raise RuntimeError(f"Failed to fetch HTML for {url}")

    async def discover_categories(self) -> list[dict[str, str]]:
        html = await self._fetch_html(HOME_URL)
        discovered = self.extract_categories_from_homepage(html)
        if discovered:
            log.progress(f"Discovered {len(discovered)} fashion category seeds from homepage")
            return discovered
        log.progress("Homepage discovery returned no categories, using static fallback")
        return STATIC_CATEGORIES

    async def fetch_products_page(
        self, category: dict[str, str], page: int = 1
    ) -> list[dict[str, Any]]:
        params = {
            "cat_id": category["cat_id"],
            "child_cat_id": category["cat_id"],
            "page": page,
            "limit": min(self.batch_size, 120),
            "_type": "entity",
            "sort": 0,
        }

        for attempt in range(3):
            try:
                loop = asyncio.get_running_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: self.cf_scraper.get(
                        LIST_API_URL,
                        params=params,
                        headers=API_HEADERS,
                        timeout=30,
                    ),
                )
                text = response.text or ""
                if response.status_code == 403 and text.strip() in {"", "{}"}:
                    raise SheinRiskChallengeError(
                        f"Listing API blocked with 403 for cat_id={category['cat_id']}"
                    )
                if self._is_risk_challenge(str(response.url), text):
                    raise SheinRiskChallengeError(
                        f"Risk challenge on listing API for cat_id={category['cat_id']}"
                    )
                response.raise_for_status()
                payload = response.json()
                if isinstance(payload, dict):
                    return (
                        payload.get("info", {}).get("products", [])
                        or payload.get("products", [])
                        or payload.get("goods_list", [])
                        or payload.get("list", [])
                        or []
                    )
                return []
            except SheinRiskChallengeError:
                self.challenge_detected = True
                raise
            except Exception as exc:
                log.request_failed(LIST_API_URL, attempt, str(exc))
                if attempt == 2:
                    return []
                await asyncio.sleep(2 ** attempt)
        return []

    @staticmethod
    def _extract_price(value: Any) -> float:
        if isinstance(value, (int, float)):
            return float(value)
        cleaned = str(value).replace("$", "").replace(",", "").replace("SGD", "").strip()
        try:
            return float(cleaned)
        except ValueError:
            return 0.0

    def transform_product(
        self, raw: dict[str, Any], category: dict[str, str]
    ) -> dict[str, Any] | None:
        try:
            sku = str(raw.get("goods_id") or raw.get("productId") or raw.get("id") or "")
            title = raw.get("goods_name") or raw.get("goods_title") or raw.get("title") or ""
            if not sku or not title:
                return None

            price = self._extract_price(
                raw.get("salePrice")
                or raw.get("retailPrice")
                or raw.get("price")
                or raw.get("shop_price")
            )
            original_price = self._extract_price(
                raw.get("marketPrice")
                or raw.get("originalPrice")
                or raw.get("retailPrice")
                or price
            )
            image_url = (
                raw.get("goods_img")
                or raw.get("goods_img_thumb")
                or raw.get("image")
                or raw.get("image_url")
                or ""
            )
            product_url = raw.get("detail_url") or raw.get("goods_url") or raw.get("url") or ""
            if product_url and not product_url.startswith("http"):
                product_url = urljoin(BASE_URL, product_url)

            discount_pct = 0
            if original_price > price > 0:
                discount_pct = round(((original_price - price) / original_price) * 100)

            return {
                "sku": sku,
                "merchant_id": MERCHANT_ID,
                "title": title,
                "description": raw.get("goods_desc") or raw.get("description") or "",
                "price": price,
                "currency": "SGD",
                "url": product_url,
                "image_url": image_url,
                "category": category["name"],
                "category_path": [category["name"], category["sub"]],
                "brand": raw.get("brand_name") or "SHEIN",
                "is_active": True,
                "metadata": {
                    "cat_id": category["cat_id"],
                    "original_price": original_price,
                    "discount_pct": discount_pct,
                    "review_count": raw.get("comment_num") or raw.get("comment_count") or 0,
                    "rating": raw.get("comment_rank_average") or raw.get("rating") or 0,
                    "goods_url_name": raw.get("goods_url_name") or "",
                },
            }
        except Exception as exc:
            log.transform_error(None, str(exc))
            return None

    def _write_products_to_file(self, products: list[dict[str, Any]]) -> None:
        if not products:
            return
        with open(self.products_outfile, "a", encoding="utf-8") as handle:
            for product in products:
                handle.write(json.dumps(product, ensure_ascii=False) + "\n")

    async def ingest_batch(self, products: list[dict[str, Any]]) -> tuple[int, int, int]:
        if not products:
            return 0, 0, 0
        if self.scrape_only:
            self._write_products_to_file(products)
            return len(products), 0, 0

        url = f"{self.api_base}/v1/ingest/products"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {"source": SOURCE, "products": products}
        try:
            response = await self.http_client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()
            return (
                result.get("rows_inserted", 0),
                result.get("rows_updated", 0),
                result.get("rows_failed", 0),
            )
        except Exception as exc:
            log.ingestion_error(url, str(exc))
            return 0, 0, len(products)

    async def scrape_category(self, category: dict[str, str]) -> dict[str, int]:
        counts = {"scraped": 0, "ingested": 0, "updated": 0, "failed": 0}
        page = 1
        batch: list[dict[str, Any]] = []

        while True:
            try:
                products = await self.fetch_products_page(category, page)
            except SheinRiskChallengeError as exc:
                log.request_failed(category["url"], page, str(exc))
                break

            if not products:
                break

            for raw in products:
                transformed = self.transform_product(raw, category)
                if not transformed:
                    continue
                batch.append(transformed)
                counts["scraped"] += 1
                if len(batch) >= self.batch_size:
                    inserted, updated, failed = await self.ingest_batch(batch)
                    counts["ingested"] += inserted
                    counts["updated"] += updated
                    counts["failed"] += failed
                    batch = []

            if len(products) < min(self.batch_size, 120):
                break

            page += 1
            await asyncio.sleep(self.delay)

        if batch:
            inserted, updated, failed = await self.ingest_batch(batch)
            counts["ingested"] += inserted
            counts["updated"] += updated
            counts["failed"] += failed

        self.total_scraped += counts["scraped"]
        self.total_ingested += counts["ingested"]
        self.total_updated += counts["updated"]
        self.total_failed += counts["failed"]
        return counts

    async def run(self) -> dict[str, Any]:
        start = time.time()
        categories = await self.discover_categories()
        if self.discover_only:
            summary = {
                "discovered_categories": len(categories),
                "sample_categories": categories[:10],
                "challenge_detected": self.challenge_detected,
                "output_file": self.products_outfile,
            }
            print(json.dumps(summary, ensure_ascii=False, indent=2))
            return summary

        for category in categories:
            await self.scrape_category(category)
            if self.challenge_detected:
                break
            await asyncio.sleep(self.delay)

        summary = {
            "elapsed_seconds": round(time.time() - start, 1),
            "total_scraped": self.total_scraped,
            "total_ingested": self.total_ingested,
            "total_updated": self.total_updated,
            "total_failed": self.total_failed,
            "challenge_detected": self.challenge_detected,
            "output_file": self.products_outfile,
            "category_count": len(categories),
        }
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return summary


async def main() -> None:
    parser = argparse.ArgumentParser(description="SHEIN SG scraper")
    parser.add_argument("--api-key", default=None, help="BuyWhere API key")
    parser.add_argument("--api-base", default="http://localhost:8000", help="BuyWhere API base URL")
    parser.add_argument("--batch-size", type=int, default=100)
    parser.add_argument("--delay", type=float, default=1.0)
    parser.add_argument("--scrape-only", action="store_true", help="Write NDJSON without ingestion")
    parser.add_argument("--discover-only", action="store_true", help="Only emit discovered category seeds")
    args = parser.parse_args()

    if not args.scrape_only and not args.discover_only and not args.api_key:
        parser.error("--api-key is required unless --scrape-only or --discover-only is specified")

    scraper = SHEINScraper(
        api_key=args.api_key or "",
        api_base=args.api_base,
        batch_size=args.batch_size,
        delay=args.delay,
        scrape_only=args.scrape_only,
        discover_only=args.discover_only,
    )
    try:
        await scraper.run()
    finally:
        await scraper.close()


if __name__ == "__main__":
    asyncio.run(main())
