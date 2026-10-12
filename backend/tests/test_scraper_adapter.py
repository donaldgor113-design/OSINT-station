from app.adapters.browser import SocialBrowserAdapter
from app.adapters.scraper import CompanyScraperAdapter


def test_company_scraper_normalizes_company():
    adapter = CompanyScraperAdapter(mock=True)
    entity = adapter.normalize_response(
        {"domain": "example.com", "title": "Example Corp"}
    )
    assert entity.entity_type == "company"
    assert entity.entity_name == "Example Corp"
    assert entity.properties.metadata.sources[0].name == "company_scraper"


def test_company_scraper_guess_domain():
    assert CompanyScraperAdapter._guess_domain("https://www.Example.com/path") == "example.com"
    assert CompanyScraperAdapter._guess_domain("example.org") == "example.org"


def test_social_browser_normalizes_document():
    adapter = SocialBrowserAdapter(mock=True)
    entity = adapter.normalize_response(
        {
            "query": "example.com",
            "url": "https://example.com",
            "title": "Example Domain",
            "content": "text",
        }
    )
    assert entity.entity_type == "document"
    assert entity.entity_name == "Example Domain"
    assert entity.properties.metadata.sources[0].name == "social_browser"


async def test_scraper_mock_returns_record():
    adapter = CompanyScraperAdapter(mock=True)
    results = await adapter.search("example.com")
    assert len(results) == 1
    assert results[0]["domain"] == "example.com"
