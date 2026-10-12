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


class AdapterRegistry:
    """Resolves an adapter by source name.

    Kept minimal for the PoC phases — later phases replace this with the
    plugin system (spec §6) that discovers adapters from disk.
    """

    _adapters: dict[str, type[Adapter]] = {}

    @classmethod
    def register(cls, adapter: type[Adapter]) -> None:
        cls._adapters[adapter.source_name] = adapter

    @classmethod
    def get(cls, name: str) -> type[Adapter] | None:
        return cls._adapters.get(name)

    @classmethod
    def available(cls) -> list[str]:
        return sorted(cls._adapters.keys())


AdapterRegistry.register(ShodanAdapter)
AdapterRegistry.register(GoogleMapsGeocodeAdapter)
AdapterRegistry.register(WhoisAdapter)
AdapterRegistry.register(TelegramAdapter)
AdapterRegistry.register(CompanyScraperAdapter)
AdapterRegistry.register(CompanyRegistryAdapter)
AdapterRegistry.register(CompanyProfileAdapter)
AdapterRegistry.register(SocialBrowserAdapter)
AdapterRegistry.register(WebSearchAdapter)
