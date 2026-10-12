from app.ai.anomalies import detect_anomalies
from app.ai.ollama import OllamaProvider


def test_no_anomalies_for_empty():
    assert detect_anomalies([]) == []


def test_stale_observation_flagged():
    entities = [
        {"name": "old-host", "observed_at": "2020-01-01T00:00:00Z", "coordinates": []},
        {"name": "fresh-host", "observed_at": None, "coordinates": []},
    ]
    anomalies = detect_anomalies(entities)
    assert any("old-host" in a for a in anomalies)


def test_geographic_outlier_flagged():
    entities = [
        {"name": "A", "coordinates": [30.5, 50.4]},
        {"name": "B", "coordinates": [30.6, 50.5]},
        {"name": "C", "coordinates": [30.4, 50.3]},
        {"name": "far", "coordinates": [120.0, -30.0]},
    ]
    anomalies = detect_anomalies(entities)
    assert any("far" in a for a in anomalies)


async def test_ollama_unreachable_degrades_gracefully():
    provider = OllamaProvider(base_url="http://127.0.0.1:1", model="llama3.2")
    text = await provider.summarize([{"name": "x", "type": "ip", "sources": ["shodan"]}])
    assert text.startswith("(Ollama недоступний")
