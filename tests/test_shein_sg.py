from scrapers.shein_sg import SHEINScraper


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
