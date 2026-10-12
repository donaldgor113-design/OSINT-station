from app.adapters.whois import WhoisAdapter


def test_normalize_domain_mock_fallback():
    adapter = WhoisAdapter(mock=True)
    raw = adapter._mock_record("example.com")
    entity = adapter.normalize_response(raw)

    assert entity.entity_type == "domain"
    assert entity.entity_name == "example.com"
    assert entity.properties.domain["registrar"] == ""
    assert entity.properties.domain["note"].startswith("RDAP недоступний")
    assert entity.properties.metadata.sources[0].name == "whois"
    assert entity.properties.metadata.sources[0].confidence == 0.5


def test_normalize_real_rdap_record():
    adapter = WhoisAdapter(mock=True)
    raw = {
        "ldhName": "EXAMPLE.COM",
        "handle": "EXAMPLE.COM",
        "status": ["active"],
        "entities": [
            {
                "roles": ["registrar"],
                "vcardArray": ["vcard", [["fn", {}, "text", "MarkMonitor Inc."]]],
            }
        ],
        "events": [{"eventAction": "expiration", "eventDate": "2026-01-01T00:00:00Z"}],
    }
    entity = adapter.normalize_response(raw)

    assert entity.properties.domain["registrar"] == "MarkMonitor Inc."
    assert entity.properties.domain["expires"].startswith("2026")
    assert entity.properties.domain["note"] == ""
    assert entity.properties.metadata.sources[0].confidence == 0.95


def test_domain_normalization_strips_url():
    assert WhoisAdapter._normalize_domain("https://www.Example.com/path") == "example.com"
    assert WhoisAdapter._normalize_domain("http://example.org") == "example.org"


def test_domain_entity_id_is_stable():
    adapter = WhoisAdapter(mock=True)
    a = adapter.normalize_response(adapter._mock_record("example.com"))
    b = adapter.normalize_response(adapter._mock_record("example.com"))
    assert a.entity_id == b.entity_id


async def test_search_mock_returns_single_record():
    adapter = WhoisAdapter(mock=True)
    results = await adapter.search("example.com")
    assert len(results) == 1
    assert results[0]["ldhName"] == "EXAMPLE.COM"
