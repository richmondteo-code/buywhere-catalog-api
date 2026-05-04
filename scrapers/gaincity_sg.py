"""
Gain City Singapore product scraper.

Uses Magento 2 GraphQL API with curl_cffi Chrome impersonation to bypass Cloudflare.
Extracts all products via pagination and normalizes to BuyWhere schema for
ingestion via /v1/ingest/products.

Site: gaincity.com (Magento 2)
Endpoint: /graphql
Strategy: Magento GraphQL products query with pagination and full field extraction.

Usage:
    python scrapers/gaincity_sg.py --api-key <key> --batch-size 100 --delay 1.5
    python scrapers/gaincity_sg.py --api-key <key> --scrape-only --limit 500

Categories: Air conditioners, Fans, Computers, Vacuum Cleaners, Smart Home,
            TVs, Water Heaters, Water Purification, Garment Care, and more.
Target: 10,865+ products (81+ product categories)
"""

import argparse
import json
import math
import os
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from curl_cffi import requests as cffi_requests
from scrapers.scraper_logging import get_logger

MERCHANT_ID = "gaincity_sg"
SOURCE = "gaincity"
BASE_URL = "https://www.gaincity.com"
GRAPHQL_URL = f"{BASE_URL}/graphql"
OUTPUT_DIR = "/home/paperclip/buywhere-api/data/gaincity"

log = get_logger(MERCHANT_ID)

GRAPHQL_PRODUCT_QUERY = """
query ($pageSize: Int!, $currentPage: Int!) {
    products(search: "", pageSize: $pageSize, currentPage: $currentPage) {
        items {
            id
            name
            sku
            url_key
            price_range {
                minimum_price {
                    regular_price { value currency }
                    final_price { value currency }
                    discount { amount_off percent_off }
                }
            }
            image { url label }
            small_image { url label }
            description { html }
            short_description { html }
            manufacturer
            categories { name url_path }
        }
        total_count
        page_info { page_size current_page total_pages }
    }
}
"""

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-SG,en;q=0.9",
    "Content-Type": "application/json",
    "Origin": BASE_URL,
    "Referer": f"{BASE_URL}/",
}

session = cffi_requests.Session()
session.headers.update(HEADERS)


def graphql_post(query, variables, retries=3):
    payload = {"query": query, "variables": variables}
    for attempt in range(retries):
        try:
            resp = session.post(
                GRAPHQL_URL, json=payload,
                impersonate="chrome120", timeout=30
            )
            if resp.status_code == 429:
                wait = 10 * (attempt + 1)
                print(f"  Rate limited, waiting {wait}s...")
                time.sleep(wait)
                continue
            if resp.status_code != 200:
                print(f"  HTTP {resp.status_code} attempt {attempt+1}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
                continue
            return json.loads(resp.text)
        except Exception as e:
            print(f"  Request error attempt {attempt+1}: {e}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
    return None


def transform_product(raw):
    try:
        name = (raw.get("name") or "").strip()
        sku = (raw.get("sku") or "").strip()
        if not name and not sku:
            return None

        pid = raw.get("id", "")
        merchant_sku = sku or f"gc_{pid}"

        price_data = raw.get("price_range", {}).get("minimum_price", {})
        final_price = price_data.get("final_price", {})
        price = float(final_price.get("value", 0) or 0)
        currency = final_price.get("currency", "SGD")

        regular_price_data = price_data.get("regular_price", {})
        regular_price = float(regular_price_data.get("value", 0) or 0)

        image_data = raw.get("image") or {}
        image_url = image_data.get("url", "") or ""
        if not image_url:
            small_image_data = raw.get("small_image") or {}
            image_url = small_image_data.get("url", "") or ""

        description_html = (raw.get("description") or {}).get("html", "") or ""
        short_description_html = (raw.get("short_description") or {}).get("html", "") or ""
        desc = description_html or short_description_html or ""

        manufacturer = raw.get("manufacturer") or ""
        categories = raw.get("categories") or []
        category_names = [c.get("name", "") for c in categories if c.get("name")]

        url_key = raw.get("url_key", "")
        product_url = f"{BASE_URL}/{url_key}" if url_key else ""

        title = name or sku
        brand = manufacturer or ""

        return {
            "sku": merchant_sku,
            "merchant_id": MERCHANT_ID,
            "title": title,
            "description": desc,
            "price": price,
            "regular_price": regular_price,
            "currency": currency,
            "url": product_url,
            "image_url": image_url,
            "category": category_names[-1] if category_names else "",
            "category_path": category_names,
            "brand": brand,
            "is_active": price > 0,
            "country_code": "SG",
            "region": "sg",
            "metadata": {
                "source_type": "magento_graphql",
                "product_id": str(pid),
                "url_key": url_key,
            },
        }
    except Exception as e:
        return None


def _post_batch(products, api_key, api_base):
    url = f"{api_base}/v1/ingest/products"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"source": SOURCE, "products": products}
    resp = session.post(url, json=payload, headers=headers, timeout=60)
    resp.raise_for_status()
    result = resp.json()
    return (
        result.get("rows_inserted", 0),
        result.get("rows_updated", 0),
        result.get("rows_failed", 0),
    )


def ingest_batch(products, api_key, api_base):
    if not products:
        return 0, 0, 0
    try:
        return _post_batch(products, api_key, api_base)
    except Exception as e:
        err = str(e)
        if "413" not in err or len(products) <= 1:
            print(f"  Ingest error: {e}")
            return 0, 0, len(products)
        half = len(products) // 2
        a_ins, a_upd, a_fail = ingest_batch(products[:half], api_key, api_base)
        b_ins, b_upd, b_fail = ingest_batch(products[half:], api_key, api_base)
        return a_ins + b_ins, a_upd + b_upd, a_fail + b_fail


def run_scraper(api_key="", api_base="http://localhost:8000", batch_size=100,
                delay=1.5, data_dir=OUTPUT_DIR, limit=0, scrape_only=False):
    Path(data_dir).mkdir(parents=True, exist_ok=True)

    print(f"Gain City SG Magento GraphQL Scraper")
    print(f"Mode: {'scrape only' if scrape_only else f'API: {api_base}'}")
    print(f"Limit: {limit if limit else 'all'}, Batch: {batch_size}, Delay: {delay}s")
    print()

    start = time.time()

    # Probe total
    first = graphql_post(GRAPHQL_PRODUCT_QUERY, {"pageSize": 1, "currentPage": 1})
    if not first:
        print("ERROR: GraphQL probe failed")
        return {"error": "GraphQL probe failed", "total_scraped": 0}

    try:
        total = first["data"]["products"]["total_count"]
        total_pages = first["data"]["products"]["page_info"]["total_pages"]
    except Exception as e:
        print(f"ERROR: Failed to parse response: {e}")
        return {"error": str(e), "total_scraped": 0}

    effective = min(limit, total) if limit else total
    pages = math.ceil(effective / batch_size)
    print(f"Total catalog: {total} products, ~{pages} pages (batch_size={batch_size})")
    if limit and limit < total:
        print(f"Limit: {limit}")

    # Fetch all products
    all_raw = []
    fetched = 0
    page = 1

    while page <= pages and (not limit or fetched < limit):
        result = graphql_post(GRAPHQL_PRODUCT_QUERY, {
            "pageSize": batch_size,
            "currentPage": page,
        })
        if not result:
            print(f"  Page {page}/{pages}: FAILED, retrying...")
            time.sleep(delay)
            result = graphql_post(GRAPHQL_PRODUCT_QUERY, {
                "pageSize": batch_size,
                "currentPage": page,
            })
            if not result:
                print(f"  Page {page}/{pages}: SKIPPED")
                page += 1
                continue

        items = result.get("data", {}).get("products", {}).get("items", [])
        if not items:
            break

        if limit:
            remaining = limit - fetched
            items = items[:remaining]

        all_raw.extend(items)
        fetched += len(items)

        if page % 20 == 0 or page == 1:
            print(f"  Page {page}/{pages}: +{len(items)} = {fetched} total")

        page += 1
        if page <= pages:
            time.sleep(delay)

    print(f"\nFetched {fetched} raw products from {page-1} pages")

    # Transform
    products = []
    transform_errors = 0
    for raw in all_raw:
        p = transform_product(raw)
        if p:
            products.append(p)
        else:
            transform_errors += 1

    print(f"Transformed: {len(products)} products ({transform_errors} errors)")

    # Ingest in batches
    total_ingested = 0
    total_updated = 0
    total_failed = 0

    if scrape_only or not api_key:
        ts = time.strftime("%Y%m%d_%H%M%S")
        outfile = os.path.join(data_dir, f"products_{ts}.jsonl")
        with open(outfile, "w", encoding="utf-8") as f:
            for p in products:
                f.write(json.dumps(p, ensure_ascii=False) + "\n")
        print(f"Wrote {len(products)} products to {outfile}")
    else:
        print(f"\nIngesting {len(products)} products...")
        for i in range(0, len(products), batch_size):
            batch = products[i:i + batch_size]
            inserted, updated, failed = ingest_batch(batch, api_key, api_base)
            total_ingested += inserted
            total_updated += updated
            total_failed += failed

            batch_num = i // batch_size + 1
            total_batches = (len(products) + batch_size - 1) // batch_size
            if batch_num % 20 == 0 or batch_num == 1:
                print(f"  Batch {batch_num}/{total_batches}: {inserted} ins, {updated} upd, {failed} fail (total: {total_ingested})")

            if i + batch_size < len(products):
                time.sleep(delay)

    elapsed = time.time() - start
    summary = {
        "merchant": MERCHANT_ID,
        "platform": "magento_graphql",
        "total_catalog": total,
        "scraped": fetched,
        "ingested": total_ingested,
        "updated": total_updated,
        "failed": total_failed,
        "transform_errors": transform_errors,
        "elapsed_seconds": round(elapsed, 1),
    }

    print(f"\nDone in {elapsed:.0f}s:")
    print(f"  Scraped: {fetched}")
    print(f"  Ingested: {total_ingested}, Updated: {total_updated}, Failed: {total_failed}")
    return summary


def main():
    parser = argparse.ArgumentParser(description="Gain City SG Magento GraphQL Scraper")
    parser.add_argument("--api-key", default="", help="BuyWhere API key")
    parser.add_argument("--api-base", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--batch-size", type=int, default=100)
    parser.add_argument("--delay", type=float, default=1.5)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--scrape-only", action="store_true")
    args = parser.parse_args()

    summary = run_scraper(
        api_key=args.api_key,
        api_base=args.api_base,
        batch_size=args.batch_size,
        delay=args.delay,
        limit=args.limit,
        scrape_only=args.scrape_only,
    )
    print(f"\n{json.dumps(summary, indent=2)}")
    return summary


if __name__ == "__main__":
    main()
