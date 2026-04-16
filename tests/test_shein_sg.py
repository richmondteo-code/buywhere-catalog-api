from scrapers.shein_sg import SHEINScraper, build_scraperapi_proxy_url


def test_extract_categories_from_homepage_filters_fashion_items():
    html = """
    <script>
    {"webClickUrl":"\\/Men-Shirt-Co-ords-c-9037.html","categoryName":"Men Shirt Co-ords"}
    {"webClickUrl":"\\/Women-Dresses-c-1727.html","categoryName":"Women Dresses"}
    {"webClickUrl":"\\/Home-Storage-c-5555.html","categoryName":"Home Storage"}
    </script>
    """

    categories = SHEINScraper.extract_categories_from_homepage(html)

    assert len(categories) == 2
    assert categories[0]["cat_id"] == "9037"
    assert categories[0]["name"] == "Men"
    assert categories[1]["cat_id"] == "1727"
    assert categories[1]["name"] == "Women"


def test_is_risk_challenge_detects_block_pages():
    blocked = SHEINScraper._is_risk_challenge(
        "https://sg.shein.com/risk/challenge?captcha_type=909",
        "<html>risk-id=abc irregular activities</html>",
    )
    clean = SHEINScraper._is_risk_challenge(
        "https://sg.shein.com/sg-en/",
        "<html>Women Dresses</html>",
    )

    assert blocked is True
    assert clean is False


def test_build_scraperapi_proxy_url():
    assert (
        build_scraperapi_proxy_url("abc123")
        == "http://scraperapi:abc123@proxy-server.scraperapi.com:8001"
    )


def test_proxy_headers_added_when_scraperapi_enabled():
    scraper = SHEINScraper(
        api_key="",
        scrape_only=True,
        discover_only=True,
        scraperapi_key="abc123",
    )
    try:
        headers = scraper._headers_with_proxy_options({"User-Agent": "Mozilla/5.0"})
        assert headers["x-sapi-render"] == "true"
        assert headers["x-sapi-country_code"] == "sg"
    finally:
        scraper.cf_scraper.close()
        scraper.request_session.close()
