from app.adapters.company_profile import CompanyProfileAdapter


def test_extract_edrpou():
    assert CompanyProfileAdapter._extract_edrpou("ЄДРПОУ 31316718") == "31316718"
    assert CompanyProfileAdapter._extract_edrpou("31316718 Нова Пошта") == "31316718"
    assert CompanyProfileAdapter._extract_edrpou("нова пошта") is None


def test_classification_helpers():
    assert CompanyProfileAdapter._is_wiki("uk.wikipedia.org")
    assert not CompanyProfileAdapter._is_wiki("example.com")
    assert CompanyProfileAdapter._social_name("www.facebook.com") == "Facebook"
    assert CompanyProfileAdapter._social_name("example.com") is None
    assert CompanyProfileAdapter._is_registry("youcontrol.com.ua")


def test_aggregate_builds_structured_profile():
    adapter = CompanyProfileAdapter(mock=True)
    results = [
        {"title": "Вікі", "url": "https://uk.wikipedia.org/wiki/Компанія", "snippet": ""},
        {"title": "FB", "url": "https://facebook.com/company", "snippet": ""},
        {"title": "Сайт", "url": "https://company.ua", "snippet": ""},
        {
            "title": "Реєстр",
            "url": "https://youcontrol.com.ua/catalog/12345678",
            "snippet": "ЄДРПОУ 12345678, м. Київ",
        },
    ]
    agg = adapter._aggregate("Компанія", results)

    assert agg["wikipedia"] == "https://uk.wikipedia.org/wiki/Компанія"
    assert agg["website"] == "https://company.ua"
    assert agg["socials"] == [{"network": "Facebook", "url": "https://facebook.com/company"}]
    assert agg["legal"]["edrpou"] == "12345678"
    assert len(agg["mentions"]) >= 1


def test_normalize_profile_structure():
    adapter = CompanyProfileAdapter(mock=True)
    entity = adapter.normalize_response(
        {
            "name": "Компанія",
            "wikipedia": "https://uk.wikipedia.org/wiki/Компанія",
            "website": "https://company.ua",
            "socials": [{"network": "Facebook", "url": "https://facebook.com/company"}],
            "mentions": [{"title": "Новина", "url": "https://example.com/1"}],
            "legal": {"edrpou": "12345678", "snippet": "..."},
        }
    )
    assert entity.entity_type == "company"
    assert entity.properties.company["wikipedia"] == "https://uk.wikipedia.org/wiki/Компанія"
    assert entity.properties.company["edrpou"] == "12345678"


def test_parse_legal_page_extracts_fields():
    adapter = CompanyProfileAdapter(mock=True)
    html = (
        "<div>ЄДРПОУ: 12345678</div>"
        "<div>Юридична адреса: Україна, м. Київ, вул. Хрещатик, 1</div>"
        "<div>Керівник: Коваленко Олексій Васильович</div>"
        "<div>Стан: зареєстрована</div>"
        "<div>Дата реєстрації: 15.03.2010</div>"
        "<div>Основний вид діяльності: 64.19 Інші види грошового посередництва</div>"
    )
    parsed = adapter._parse_legal_page(html)
    assert parsed["edrpou"] == "12345678"
    assert "Київ" in parsed.get("address", "")
    assert parsed.get("director") == "Коваленко Олексій Васильович"
    assert parsed.get("status") == "зареєстрована"
    assert parsed.get("registered_at") == "15.03.2010"
    assert parsed.get("activities")
