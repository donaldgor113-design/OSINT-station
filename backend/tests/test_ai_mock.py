from app.ai.mock import MockAIProvider


async def test_summarize_empty():
    text = await MockAIProvider().summarize([])
    assert "Немає даних" in text


async def test_summarize_breaks_down_types():
    entities = [
        {"type": "ip", "name": "1.1.1.1", "sources": ["shodan"], "country": "AU"},
        {"type": "ip", "name": "8.8.8.8", "sources": ["shodan"], "country": "US"},
        {"type": "location", "name": "Київ", "sources": ["google_maps"], "country": "Україна"},
    ]
    text = await MockAIProvider().summarize(entities)
    assert "ip" in text
    assert "location" in text
    assert "shodan" in text
    assert "google_maps" in text


async def test_cross_check_flags_corroborated():
    entities = [
        {"name": "A", "sources": ["shodan", "google_maps"]},
        {"name": "B", "sources": ["shodan"]},
    ]
    text = await MockAIProvider().cross_check(entities)
    assert "кількома джерелами" in text
    assert "A" in text
