from app.adapters.google_maps import GoogleMapsGeocodeAdapter

SAMPLE_PLACE = {
    "formatted_address": "Київ, Україна, 01001",
    "geometry": {"location": {"lat": 50.4501, "lng": 30.5234}},
    "address_components": [
        {"long_name": "Київ", "types": ["locality", "political"]},
        {"long_name": "Україна", "types": ["country", "political"]},
    ],
}


def test_normalize_maps_location_fields():
    entity = GoogleMapsGeocodeAdapter(mock=True).normalize_response(SAMPLE_PLACE)

    assert entity.entity_type == "location"
    assert entity.entity_name == "Київ, Україна, 01001"
    assert entity.properties.geo.city == "Київ"
    assert entity.properties.geo.country == "Україна"
    assert entity.properties.geo.coordinates == [30.5234, 50.4501]
    assert entity.properties.metadata.sources[0].name == "google_maps"


def test_location_entity_id_rounds_coordinates():
    adapter = GoogleMapsGeocodeAdapter(mock=True)
    a = adapter.normalize_response(
        {"formatted_address": "X", "geometry": {"location": {"lat": 50.45011, "lng": 30.52341}}}
    )
    b = adapter.normalize_response(
        {"formatted_address": "X", "geometry": {"location": {"lat": 50.45014, "lng": 30.52344}}}
    )
    # Nearly identical coordinates -> same entity (dedup), spec §4.
    assert a.entity_id == b.entity_id


async def test_search_mock_returns_places():
    adapter = GoogleMapsGeocodeAdapter(mock=True)
    results = await adapter.search("Київ")
    assert len(results) == 2
    assert all("geometry" in r for r in results)
