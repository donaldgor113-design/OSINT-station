from app.adapters.shodan import ShodanAdapter

SAMPLE_MATCH = {
    "ip_str": "185.199.108.153",
    "port": 443,
    "org": "GitHub, Inc.",
    "location": {
        "city": "Frankfurt am Main",
        "country_name": "Germany",
        "latitude": 50.1109,
        "longitude": 8.6821,
    },
    "product": "nginx",
    "data": "HTTP/1.1 200 OK",
}


def test_normalize_response_maps_identity_fields():
    entity = ShodanAdapter().normalize_response(SAMPLE_MATCH)

    assert entity.entity_type == "ip"
    assert entity.entity_name == "185.199.108.153"
    assert entity.entity_id is not None


def test_normalize_response_maps_geo():
    entity = ShodanAdapter().normalize_response(SAMPLE_MATCH)

    assert entity.properties.geo.city == "Frankfurt am Main"
    assert entity.properties.geo.country == "Germany"
    assert entity.properties.geo.coordinates == [8.6821, 50.1109]


def test_normalize_response_maps_footprint_and_source():
    entity = ShodanAdapter().normalize_response(SAMPLE_MATCH)

    assert entity.properties.digital_footprint.ip_addresses == ["185.199.108.153"]
    assert entity.properties.metadata.sources[0].name == "shodan"
    assert entity.properties.metadata.sources[0].confidence == 0.9


def test_normalize_response_keeps_raw_data():
    entity = ShodanAdapter().normalize_response(SAMPLE_MATCH)
    assert entity.raw_data["shodan"]["ip_str"] == "185.199.108.153"


def test_normalize_response_is_stable_across_runs():
    a = ShodanAdapter().normalize_response(SAMPLE_MATCH)
    b = ShodanAdapter().normalize_response(SAMPLE_MATCH)
    assert a.entity_id == b.entity_id


async def test_search_mock_returns_sample_results():
    adapter = ShodanAdapter(mock=True)
    results = await adapter.search("nginx")
    assert len(results) == 3
    assert all("ip_str" in r for r in results)


async def test_search_without_key_and_mock_returns_empty():
    adapter = ShodanAdapter(api_key="", mock=False)
    results = await adapter.search("nginx")
    assert results == []
