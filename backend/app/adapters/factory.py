from ..config import get_settings
from .base import Adapter
from .browser import SocialBrowserAdapter
from .company_profile import CompanyProfileAdapter
from .company_registry import CompanyRegistryAdapter
from .google_maps import GoogleMapsGeocodeAdapter
from .scraper import CompanyScraperAdapter
from .shodan import ShodanAdapter
from .telegram import TelegramAdapter
from .web_search import WebSearchAdapter
from .whois import WhoisAdapter


def build_adapter(name: str) -> Adapter | None:
    """Construct the adapter for a source, wired to settings."""
    settings = get_settings()
    if name == "shodan":
        return ShodanAdapter(api_key=settings.shodan_api_key, mock=settings.shodan_mock)
    if name == "google_maps":
        return GoogleMapsGeocodeAdapter(
            api_key=settings.google_maps_api_key, mock=settings.google_maps_mock
        )
    if name == "whois":
        return WhoisAdapter(mock=settings.whois_mock)
    if name == "telegram":
        return TelegramAdapter(
            bot_token=settings.telegram_bot_token, mock=settings.telegram_mock
        )
    if name == "company_scraper":
        return CompanyScraperAdapter(mock=settings.scraper_mock)
    if name == "company_registry":
        return CompanyRegistryAdapter(mock=True)
    if name == "company_profile":
        return CompanyProfileAdapter(mock=False)
    if name == "social_browser":
        return SocialBrowserAdapter(mock=settings.browser_mock)
    if name == "web_search":
        return WebSearchAdapter(mock=settings.web_search_mock)
    return None
