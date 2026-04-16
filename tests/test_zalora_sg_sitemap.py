import json
import sys
from pathlib import Path

sys.path.insert(0, "/home/paperclip/buywhere-api")

from scrapers.zalora_sg_sitemap import SitemapEntry, ZaloraSitemapScraper


def test_load_existing_product_ids_supports_current_baseline_shape(tmp_path):
    baseline = tmp_path / "zalora_sg_20260416.ndjson"
    baseline.write_text(
        "\n".join(
            [
                json.dumps({"product_id": "zalora_sg_459942"}),
                json.dumps({"sku": "zalora_sg_123456"}),
                json.dumps({"metadata": {"product_id": "zalora_sg_777"}}),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    scraper = ZaloraSitemapScraper(
        output_file=str(tmp_path / "fresh.ndjson"),
        coverage_report=str(tmp_path / "coverage.json"),
        resume_from=[str(baseline)],
    )

    loaded = scraper.load_existing_product_ids()

    assert loaded == 3
    assert scraper.existing_product_ids == {"459942", "123456", "777"}


def test_parse_product_page_extracts_priced_product_from_next_data(tmp_path):
    scraper = ZaloraSitemapScraper(
        output_file=str(tmp_path / "fresh.ndjson"),
        coverage_report=str(tmp_path / "coverage.json"),
    )
    entry = SitemapEntry(
        shard="product-sitemap-1.xml",
        slug="birkenstock-milano-bf-black-459942",
        image_url="https://static-sg.zacdn.com/p/birkenstock-7959-249954-1.jpg",
    )
    html = """
    <html>
      <script id="__NEXT_DATA__" type="application/json">
      {
        "props": {
          "pageProps": {
            "preloadedState": {
              "pdv": {
                "product": {
                  "Name": "Milano BF",
                  "Brand": "Birkenstock",
                  "Price": "169.00",
                  "Url": "https://www.zalora.sg/p/birkenstock-milano-bf-black-459942",
                  "Attributes": {
                    "heel_height": "flat"
                  },
                  "Simples": [
                    {
                      "Price": "169.00",
                      "StockStatus": 1,
                      "FulfillmentInformation": {
                        "SellerName": "ZALORA"
                      }
                    }
                  ]
                }
              }
            }
          }
        }
      }
      </script>
    </html>
    """

    product = scraper._parse_product_page(html, entry)

    assert product is not None
    assert product["product_id"] == "zalora_sg_459942"
    assert product["name"] == "Milano BF"
    assert product["price"]["amount"] == 169.0
    assert product["category"] == "Shoes"
    assert product["merchant_id"] == "zalora"
    assert product["image_url"] == entry.image_url
