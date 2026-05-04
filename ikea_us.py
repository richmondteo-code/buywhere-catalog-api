#!/usr/bin/env python3
"""
IKEA US product scraper.

Uses BrightData residential proxy to bypass Cloudflare on ikea.com.
Scrapes category pages → discovers product IDs → fetches product details.
Resumes via seen_products.json.

Usage:
    python3 ikea_us.py --limit 50000 --delay 0.4 --concurrency 4 --timeout 30000

Output: data/ikea-us/ikea_us_YYYYMMDD.ndjson
"""

import argparse
import asyncio
import json
import os
import re
import time
import urllib.parse
from typing import Any, Optional

import httpx

MERCHANT_ID = "ikea_us"
SOURCE = "ikea_us"
BASE_URL = "https://www.ikea.com/us/en"
OUTPUT_DIR = "/home/paperclip/buywhere-api/data/ikea-us"
SEEN_FILE = os.path.join(OUTPUT_DIR, "seen_products.json")

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}

CATEGORIES = [
    {"id": "living-room",          "name": "Living Room",          "url": "https://www.ikea.com/us/en/cat/living-room/"},
    {"id": "living-room-seating",  "name": "Living Room Seating",  "url": "https://www.ikea.com/us/en/cat/living-room-seating/"},
    {"id": "tables-desks",         "name": "Tables & Desks",       "url": "https://www.ikea.com/us/en/cat/tables-desks/"},
    {"id": "chairs",               "name": "Chairs",               "url": "https://www.ikea.com/us/en/cat/chairs/"},
    {"id": "bedroom",              "name": "Bedroom",              "url": "https://www.ikea.com/us/en/cat/bedroom/"},
    {"id": "beds",                 "name": "Beds",                 "url": "https://www.ikea.com/us/en/cat/beds/"},
    {"id": "mattresses",           "name": "Mattresses",           "url": "https://www.ikea.com/us/en/cat/mattresses/"},
    {"id": "wardrobes",            "name": "Wardrobes",            "url": "https://www.ikea.com/us/en/cat/wardrobes/"},
    {"id": "bedroom-textiles",     "name": "Bedroom Textiles",     "url": "https://www.ikea.com/us/en/cat/bedroom-textiles/"},
    {"id": "kitchen",              "name": "Kitchen",              "url": "https://www.ikea.com/us/en/cat/kitchen/"},
    {"id": "kitchen-cabinets",     "name": "Kitchen Cabinets",     "url": "https://www.ikea.com/us/en/cat/kitchen-cabinets/"},
    {"id": "kitchen-appliances",   "name": "Kitchen Appliances",   "url": "https://www.ikea.com/us/en/cat/kitchen-appliances/"},
    {"id": "kitchen-knobs",        "name": "Kitchen Knobs",        "url": "https://www.ikea.com/us/en/cat/kitchen-knobs-handles/"},
    {"id": "kitchen-taps",         "name": "Kitchen Taps & Sinks", "url": "https://www.ikea.com/us/en/cat/kitchen-taps-sinks/"},
    {"id": "cookware",             "name": "Cookware",             "url": "https://www.ikea.com/us/en/cat/cookware/"},
    {"id": "tableware",            "name": "Tableware",            "url": "https://www.ikea.com/us/en/cat/tableware/"},
    {"id": "food-beverages",       "name": "Food & Beverages",     "url": "https://www.ikea.com/us/en/cat/food-beverages/"},
    {"id": "dining",               "name": "Dining",               "url": "https://www.ikea.com/us/en/cat/dining/"},
    {"id": "bathroom",             "name": "Bathroom",             "url": "https://www.ikea.com/us/en/cat/bathroom/"},
    {"id": "bathroom-furniture",   "name": "Bathroom Furniture",   "url": "https://www.ikea.com/us/en/cat/bathroom-furniture/"},
    {"id": "bathroom-textiles",    "name": "Bathroom Textiles",    "url": "https://www.ikea.com/us/en/cat/bathroom-textiles/"},
    {"id": "home-office",          "name": "Home Office",          "url": "https://www.ikea.com/us/en/cat/home-office/"},
    {"id": "office-chairs",        "name": "Office Chairs",        "url": "https://www.ikea.com/us/en/cat/office-chairs/"},
    {"id": "office-desks",         "name": "Office Desks",         "url": "https://www.ikea.com/us/en/cat/office-desks/"},
    {"id": "storage",              "name": "Storage",              "url": "https://www.ikea.com/us/en/cat/storage-organization/"},
    {"id": "shelving-units",       "name": "Shelving Units",       "url": "https://www.ikea.com/us/en/cat/shelving-units/"},
    {"id": "bookcases",            "name": "Bookcases",            "url": "https://www.ikea.com/us/en/cat/bookcases/"},
    {"id": "boxes-baskets",        "name": "Boxes & Baskets",      "url": "https://www.ikea.com/us/en/cat/boxes-baskets/"},
    {"id": "outdoor",              "name": "Outdoor",              "url": "https://www.ikea.com/us/en/cat/outdoor/"},
    {"id": "outdoor-furniture",    "name": "Outdoor Furniture",    "url": "https://www.ikea.com/us/en/cat/outdoor-furniture/"},
    {"id": "outdoor-gardening",    "name": "Outdoor Gardening",    "url": "https://www.ikea.com/us/en/cat/outdoor-gardening/"},
    {"id": "baby-children",        "name": "Baby & Children",      "url": "https://www.ikea.com/us/en/cat/baby-children/"},
    {"id": "childrens-furniture",  "name": "Children's Furniture", "url": "https://www.ikea.com/us/en/cat/childrens-furniture/"},
    {"id": "childrens-toys",       "name": "Children's Toys",      "url": "https://www.ikea.com/us/en/cat/childrens-toys/"},
    {"id": "textiles-rugs",        "name": "Textiles & Rugs",      "url": "https://www.ikea.com/us/en/cat/textiles-rugs/"},
    {"id": "rugs",                 "name": "Rugs",                 "url": "https://www.ikea.com/us/en/cat/rugs/"},
    {"id": "curtains-blinds",      "name": "Curtains & Blinds",    "url": "https://www.ikea.com/us/en/cat/curtains-blinds/"},
    {"id": "cushions-pillows",     "name": "Cushions & Pillows",   "url": "https://www.ikea.com/us/en/cat/cushions-pillows/"},
    {"id": "lighting",             "name": "Lighting",             "url": "https://www.ikea.com/us/en/cat/lighting/"},
    {"id": "ceiling-lights",       "name": "Ceiling Lights",       "url": "https://www.ikea.com/us/en/cat/ceiling-lights/"},
    {"id": "floor-lamps",          "name": "Floor Lamps",          "url": "https://www.ikea.com/us/en/cat/floor-lamps/"},
    {"id": "table-lamps",          "name": "Table Lamps",          "url": "https://www.ikea.com/us/en/cat/table-lamps/"},
    {"id": "smart-lighting",       "name": "Smart Lighting",       "url": "https://www.ikea.com/us/en/cat/smart-lighting/"},
    {"id": "home-decor",           "name": "Home Decor",           "url": "https://www.ikea.com/us/en/cat/home-decor/"},
    {"id": "wall-decoration",      "name": "Wall Decoration",      "url": "https://www.ikea.com/us/en/cat/wall-decoration/"},
    {"id": "mirrors",              "name": "Mirrors",              "url": "https://www.ikea.com/us/en/cat/mirrors/"},
    {"id": "plants-plant-pots",    "name": "Plants & Plant Pots",  "url": "https://www.ikea.com/us/en/cat/plants-plant-pots/"},
    {"id": "candles-fragrances",   "name": "Candles & Fragrances", "url": "https://www.ikea.com/us/en/cat/candles-fragrances/"},
    {"id": "frames-decorations",   "name": "Frames & Decorations", "url": "https://www.ikea.com/us/en/cat/frames-decorations/"},
    {"id": "laundry-cleaning",     "name": "Laundry & Cleaning",   "url": "https://www.ikea.com/us/en/cat/laundry-cleaning/"},
    {"id": "home-electronics",     "name": "Home Electronics",     "url": "https://www.ikea.com/us/en/cat/home-electronics/"},
    {"id": "pet-products",         "name": "Pet Products",         "url": "https://www.ikea.com/us/en/cat/pet-products/"},
    {"id": "holiday",              "name": "Holiday & Seasonal",   "url": "https://www.ikea.com/us/en/cat/holiday-seasonal/"},
    {"id": "tools-hardware",       "name": "Tools & Hardware",     "url": "https://www.ikea.com/us/en/cat/tools-hardware/"},
    {"id": "workshop-garage",      "name": "Workshop & Garage",    "url": "https://www.ikea.com/us/en/cat/workshop-garage/"},
]


def _build_brightdata_proxy_url() -> str:
    username = os.environ.get("BRIGHTDATA_USERNAME", "brd-customer-hl_3ab737be-zone-residential")
    password = os.environ.get("BRIGHTDATA_PASSWORD", "o3feuq72olm5")
    host = os.environ.get("BRIGHTDATA_PROXY_HOST", "brd.superproxy.io")
    port = os.environ.get("BRIGHTDATA_PROXY_PORT", "33335")
    encoded_user = urllib.parse.quote(username, safe="")
    encoded_pass = urllib.parse.quote(password, safe="")
    return f"http://{encoded_user}:{encoded_pass}@{host}:{port}"


def _extract_product_ids_from_page(html: str) -> list[str]:
    """Extract product IDs from an IKEA category/listing page."""
    ids: set[str] = set()
    # Primary pattern: product ID in data attributes or JSON
    for match in re.finditer(r'"productId"\s*:\s*"(\d+)"', html):
        ids.add(match.group(1))
    for match in re.finditer(r'"id"\s*:\s*"([a-z]?\d{3,}\.\d+)"', html):
        ids.add(match.group(1))
    # URLs like /us/en/p/name-artno/
    for match in re.finditer(r'/us/en/p/[^/]+/([a-z]?\d{3,}\.\d+)', html):
        ids.add(match.group(1))
    # URLs like /us/en/p/name-artno
    for match in re.finditer(r'href="(/us/en/p/[^"]+)"', html):
        url = match.group(1)
        m2 = re.search(r'/p/[^/]+/([a-z]?\d{3,}\.\d+)', url)
        if m2:
            ids.add(m2.group(1))
    return list(ids)


def _extract_product_data(html: str, url: str, category_name: str) -> Optional[dict[str, Any]]:
    """Extract product data from an IKEA product page, primarily from __INITIAL_STATE__."""
    try:
        product_id = ""
        title = ""
        description = ""
        price = 0.0
        image_url = ""
        currency = "USD"
        availability = True
        measurement = ""
        color = ""
        article_number = ""

        # Try __INITIAL_STATE__ first (most reliable)
        init_match = re.search(
            r'window\.__INITIAL_STATE__\s*=\s*(\{.*?\});\s*</script>', html, re.DOTALL
        )
        if not init_match:
            init_match = re.search(
                r'__INITIAL_STATE__\s*=\s*(\{.*?\});', html, re.DOTALL
            )

        if init_match:
            try:
                state = json.loads(init_match.group(1))
                product_data = None

                # Navigate the state to find product
                if isinstance(state, dict):
                    for key in ("product", "item", "items"):
                        if key in state:
                            product_data = state[key]
                            break
                    if not product_data:
                        # Try deeper paths
                        for path_str in [
                            ["product", "product"],
                            ["catalog", "product"],
                            ["page", "product"],
                        ]:
                            d = state
                            for k in path_str:
                                if isinstance(d, dict):
                                    d = d.get(k, {})
                            if isinstance(d, dict) and d:
                                product_data = d
                                break

                if isinstance(product_data, dict) and product_data:
                    title = product_data.get("name", "") or product_data.get("displayName", "") or ""
                    if not title:
                        title = product_data.get("typeName", "")
                    title = str(title).strip()

                    desc_raw = product_data.get("productDesc", "") or product_data.get("description", "")
                    if isinstance(desc_raw, dict):
                        description = desc_raw.get("html", "") or desc_raw.get("text", "")
                    else:
                        description = str(desc_raw)

                    pid = product_data.get("id", "") or product_data.get("productId", "")
                    if pid:
                        product_id = str(pid)
                        if "." in product_id and not product_id.startswith("s"):
                            pass

                    # Price from nested structure
                    price_info = product_data.get("price", {}) or product_data.get("prices", {})
                    if isinstance(price_info, dict):
                        # Try current price first
                        current = price_info.get("current", {}) or price_info.get("salesPrice", {}) or price_info
                        if isinstance(current, dict):
                            price_val = current.get("value", current.get("raw", 0))
                            currency = str(current.get("currencyCode", "USD") or "USD")
                        else:
                            price_val = price_info.get("raw", 0) or price_info.get("value", 0)
                        if isinstance(price_val, (int, float)) and price_val > 0:
                            price = float(price_val) / 100.0 if price_val > 1000000 else float(price_val)
                        elif isinstance(price_val, str):
                            price = _parse_price_string(price_val)
                    elif isinstance(price_info, (int, float)):
                        price = float(price_info) / 100.0 if float(price_info) > 1000000 else float(price_info)

                    # Images
                    images = product_data.get("images", []) or product_data.get("media", [])
                    if isinstance(images, list) and images:
                        first = images[0]
                        if isinstance(first, dict):
                            image_url = first.get("url", "") or first.get("src", "")
                            if image_url and not image_url.startswith("http"):
                                image_url = ""
                        elif isinstance(first, str):
                            image_url = first if first.startswith("http") else ""

                    # Availability
                    avail = product_data.get("availability", {}) or product_data.get("stockAvailability", {})
                    if isinstance(avail, dict):
                        status = avail.get("code", "") or avail.get("status", "")
                        if "notBuyable" in str(status) or "outOfStock" in str(status):
                            availability = False

                    # Measurement
                    measure = product_data.get("measurements", "")
                    if isinstance(measure, dict):
                        measurement = measure.get("metric", "") or measure.get("imperial", "")
                    elif isinstance(measure, str):
                        measurement = measure

                    # Color
                    color_info = product_data.get("color", "")
                    if isinstance(color_info, dict):
                        color = color_info.get("displayName", "") or color_info.get("name", "")
                    elif isinstance(color_info, str):
                        color = color_info

                    # Article number
                    art_no = product_data.get("articleNumber", "") or product_data.get("itemNumber", "")
                    if art_no:
                        article_number = str(art_no)
            except (json.JSONDecodeError, Exception) as e:
                pass

        # If __INITIAL_STATE__ didn't give us enough, fall back to HTML meta tags
        if not title:
            title_match = re.search(r'<title>([^<]+)</title>', html)
            if title_match:
                title = title_match.group(1).strip()
                title = re.sub(r'\s*\|\s*IKEA[^|]*$', '', title).strip()

        if not description:
            desc_match = re.search(r'<meta[^>]+name="description"[^>]+content="([^"]+)"', html)
            if desc_match:
                description = desc_match.group(1)

        if not image_url:
            img_match = re.search(r'<meta[^>]+property="og:image"[^>]+content="([^"]+)"', html)
            if img_match:
                image_url = img_match.group(1)

        if price <= 0:
            # Try regex-based price extraction from HTML
            price_match = re.search(r'\$\s*([\d,]+(?:\.\d{2})?)', html)
            if price_match:
                price = _parse_price_string(price_match.group(1))
            if price <= 0:
                # Try JSON embedded price
                json_price_match = re.search(r'"price"\s*:\s*(\d+(?:\.\d+)?)', html)
                if json_price_match:
                    price = float(json_price_match.group(1))
                    if price > 1000000:
                        price = price / 100.0

        if not product_id:
            pid_match = re.search(r'/us/en/p/[^/]+/([a-z]?\d{3,}\.\d+)', url)
            if pid_match:
                product_id = pid_match.group(1)

        if not title and not product_id:
            return None

        sku = f"IKEA_US_{product_id}" if product_id else f"IKEA_US_{re.sub(r'[^a-zA-Z0-9]', '', title)[:40]}"

        metadata = {
            "source": SOURCE,
            "product_id": product_id,
            "scrape_url": url,
        }
        if article_number:
            metadata["article_number"] = article_number
        if measurement:
            metadata["measurement"] = measurement
        if color:
            metadata["color"] = color
        metadata["_scraped_at"] = int(time.time())

        return {
            "sku": sku,
            "merchant_id": MERCHANT_ID,
            "title": title,
            "description": description[:2000] if description else "",
            "price": price,
            "currency": currency,
            "url": url,
            "image_url": image_url,
            "category": category_name,
            "brand": "IKEA",
            "is_active": True,
            "is_available": availability,
            "in_stock": availability,
            "metadata": metadata,
        }
    except Exception:
        return None


def _parse_price_string(s: str) -> float:
    s = s.replace(",", "").replace("$", "").replace("USD", "").strip()
    match = re.search(r"[\d]+(?:\.\d+)?", s)
    if match:
        try:
            return float(match.group(0))
        except ValueError:
            return 0.0
    return 0.0


class IKEAUSScraper:
    def __init__(
        self,
        limit: int = 50000,
        delay: float = 0.4,
        concurrency: int = 4,
        timeout: int = 30000,
        scrape_only: bool = True,
    ):
        self.limit = limit
        self.delay = delay
        self.concurrency = concurrency
        self.timeout_ms = timeout
        self.scrape_only = scrape_only
        self.total_scraped = 0
        self.total_errors = 0
        self._semaphore = asyncio.Semaphore(concurrency)
        self._seen_ids: set[str] = set()
        self._session_start = time.strftime("%Y%m%d_%H%M%S")
        self._lock = asyncio.Lock()

        os.makedirs(OUTPUT_DIR, exist_ok=True)
        self._output_file = os.path.join(OUTPUT_DIR, f"ikea_us_{time.strftime('%Y%m%d')}.ndjson")
        self._load_seen()

        proxy_url = _build_brightdata_proxy_url()
        self.client = httpx.AsyncClient(
            timeout=float(timeout) / 1000.0,
            headers=BROWSER_HEADERS,
            proxy=proxy_url,
            follow_redirects=True,
        )

    def _load_seen(self):
        if os.path.exists(SEEN_FILE):
            try:
                data = json.load(open(SEEN_FILE))
                if isinstance(data, list):
                    self._seen_ids = set(data)
                    print(f"Loaded {len(self._seen_ids)} seen product IDs from {SEEN_FILE}")
                elif isinstance(data, dict):
                    ids = data.get("ids", data.get("seen", []))
                    self._seen_ids = set(ids)
                    print(f"Loaded {len(self._seen_ids)} seen product IDs from {SEEN_FILE}")
            except Exception:
                print(f"Could not load seen file, starting fresh")
                self._seen_ids = set()
        else:
            self._seen_ids = set()

    def _save_seen(self):
        try:
            with open(SEEN_FILE, "w") as f:
                json.dump({"ids": list(self._seen_ids), "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"), "count": len(self._seen_ids)}, f)
        except Exception as e:
            print(f"Warning: could not save seen file: {e}")

    async def close(self):
        self._save_seen()
        await self.client.aclose()

    async def _fetch_page(self, url: str, retries: int = 3) -> Optional[str]:
        async with self._semaphore:
            for attempt in range(retries):
                try:
                    resp = await self.client.get(url)
                    if resp.status_code == 200:
                        return resp.text
                    elif resp.status_code in (403, 429):
                        wait = 2 ** attempt * 5
                        print(f"  HTTP {resp.status_code} for {url}, waiting {wait}s...")
                        await asyncio.sleep(wait)
                    elif resp.status_code == 503:
                        wait = 2 ** attempt * 3
                        print(f"  HTTP 503 for {url}, waiting {wait}s...")
                        await asyncio.sleep(wait)
                    else:
                        print(f"  HTTP {resp.status_code} for {url}, attempt {attempt+1}/{retries}")
                        if attempt < retries - 1:
                            await asyncio.sleep(2 ** attempt)
                        else:
                            return None
                except Exception as e:
                    print(f"  Error fetching {url}: {e}")
                    if attempt < retries - 1:
                        await asyncio.sleep(2 ** attempt)
                    else:
                        return None
            return None

    def _write_product(self, product: dict):
        with open(self._output_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(product, ensure_ascii=False) + "\n")

    async def scrape_category(self, category: dict) -> dict[str, int]:
        cat_id = category["id"]
        cat_name = category["name"]

        print(f"\n[{cat_name}] Starting... pid={os.getpid()}")
        counts = {"scraped": 0, "errors": 0}

        html = await self._fetch_page(category["url"])
        if not html:
            print(f"  [{cat_name}] Failed to fetch category page")
            return counts

        product_ids = _extract_product_ids_from_page(html)
        print(f"  [{cat_name}] Found {len(product_ids)} raw product IDs on page")

        new_ids = [pid for pid in product_ids if pid not in self._seen_ids]
        if not new_ids:
            print(f"  [{cat_name}] All {len(product_ids)} products already seen, skipping")
            return counts

        print(f"  [{cat_name}] {len(new_ids)} new products to scrape")

        sem = asyncio.Semaphore(self.concurrency)

        async def fetch_one(pid: str):
            async with sem:
                product_url = f"https://www.ikea.com/us/en/p/{pid}"
                product_html = await self._fetch_page(product_url)
                if not product_html:
                    async with self._lock:
                        counts["errors"] += 1
                        self.total_errors += 1
                    return

                product_data = _extract_product_data(product_html, product_url, cat_name)
                if not product_data:
                    async with self._lock:
                        counts["errors"] += 1
                        self.total_errors += 1
                    return

                async with self._lock:
                    self._seen_ids.add(pid)
                    self._write_product(product_data)
                    counts["scraped"] += 1
                    self.total_scraped += 1

                    if self.total_scraped % 100 == 0:
                        print(f"  [{cat_name}] Progress: {self.total_scraped} total scraped, {self.total_errors} errors")
                        self._save_seen()

                await asyncio.sleep(self.delay)

        tasks = []
        for pid in new_ids:
            if self.limit > 0 and self.total_scraped >= self.limit:
                break
            tasks.append(asyncio.create_task(fetch_one(pid)))

        if tasks:
            await asyncio.gather(*tasks)

        self._save_seen()
        print(f"  [{cat_name}] Done: scraped={counts['scraped']}, errors={counts['errors']}")
        return counts

    async def run(self) -> dict[str, Any]:
        print(f"IKEA US Scraper starting...")
        print(f"Limit: {self.limit}, Delay: {self.delay}s, Concurrency: {self.concurrency}")
        print(f"Timeout: {self.timeout_ms}ms")
        print(f"Output: {self._output_file}")
        print(f"Seen file: {SEEN_FILE} ({len(self._seen_ids)} IDs loaded)")
        print(f"Categories: {len(CATEGORIES)}")

        start = time.time()

        for category in CATEGORIES:
            if self.limit > 0 and self.total_scraped >= self.limit:
                print(f"\nLimit of {self.limit} products reached, stopping.")
                break
            await self.scrape_category(category)
            await asyncio.sleep(1)

        self._save_seen()
        elapsed = time.time() - start

        summary = {
            "elapsed_seconds": round(elapsed, 1),
            "total_scraped": self.total_scraped,
            "total_errors": self.total_errors,
            "seen_ids_count": len(self._seen_ids),
            "output_file": self._output_file,
            "seen_file": SEEN_FILE,
        }

        print(f"\n{'='*60}")
        print(f"IKEA US Scrape Complete")
        print(f"Total scraped: {self.total_scraped}")
        print(f"Total errors: {self.total_errors}")
        print(f"Seen IDs: {len(self._seen_ids)}")
        print(f"Elapsed: {elapsed:.1f}s ({elapsed/60:.1f} min)")
        print(f"Output: {self._output_file}")
        print(f"{'='*60}")
        return summary


async def main():
    parser = argparse.ArgumentParser(description="IKEA US product scraper")
    parser.add_argument("--limit", type=int, default=50000, help="Max products to scrape")
    parser.add_argument("--delay", type=float, default=0.4, help="Delay between product requests (seconds)")
    parser.add_argument("--concurrency", type=int, default=4, help="Concurrency level")
    parser.add_argument("--timeout", type=int, default=30000, help="HTTP timeout in milliseconds")
    args = parser.parse_args()

    scraper = IKEAUSScraper(
        limit=args.limit,
        delay=args.delay,
        concurrency=args.concurrency,
        timeout=args.timeout,
    )
    try:
        await scraper.run()
    finally:
        await scraper.close()


if __name__ == "__main__":
    asyncio.run(main())
