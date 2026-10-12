from app.adapters.company_registry import CompanyRegistryAdapter


def test_company_normalize_structure():
    adapter = CompanyRegistryAdapter(mock=True)
    raw = adapter._record(edrpou="12345678", name="ТОВ Приклад")
    entity = adapter.normalize_response(raw)

    assert entity.entity_type == "company"
    assert entity.entity_name == "ТОВ Приклад"
    company = entity.properties.company
    assert company["edrpou"] == "12345678"
    assert company["address"]
    assert company["director"]
    assert company["socials"]
    assert company["mentions"]
    assert company["website"]


def test_edrpou_detection():
    assert CompanyRegistryAdapter._is_edrpou("12345678")
    assert not CompanyRegistryAdapter._is_edrpou("Приклад")
    assert not CompanyRegistryAdapter._is_edrpou("123")


async def test_search_by_edrpou():
    adapter = CompanyRegistryAdapter(mock=True)
    results = await adapter.search("12345678")
    assert len(results) == 1
    assert results[0]["edrpou"] == "12345678"


async def test_search_by_name():
    adapter = CompanyRegistryAdapter(mock=True)
    results = await adapter.search("Приклад")
    assert len(results) == 1
    assert len(results[0]["edrpou"]) == 8
