from app.adapters.telegram import TelegramAdapter


def test_normalize_channel():
    entity = TelegramAdapter(mock=True).normalize_response(
        {"kind": "channel", "username": "news", "title": "News Channel"}
    )

    assert entity.entity_type == "channel"
    assert entity.entity_name == "News Channel"
    assert entity.properties.digital_footprint.social_accounts == ["t.me/news"]
    assert entity.properties.metadata.sources[0].name == "telegram"


def test_normalize_person():
    entity = TelegramAdapter(mock=True).normalize_response(
        {"kind": "person", "username": "admin", "full_name": "Admin", "phone": "+380000000000"}
    )

    assert entity.entity_type == "person"
    assert entity.entity_name == "Admin"
    assert entity.properties.digital_footprint.phones == ["+380000000000"]


async def test_search_mock_returns_channel_and_person():
    adapter = TelegramAdapter(mock=True)
    results = await adapter.search("test")
    assert len(results) == 2
    kinds = {r["kind"] for r in results}
    assert kinds == {"channel", "person"}
