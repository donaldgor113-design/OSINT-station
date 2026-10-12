import httpx


async def forward_geocode(address: str) -> dict | None:
    """Address -> coordinates via Nominatim (free, no key).

    Returns {"lat", "lng"} or None.
    """
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": address, "format": "jsonv2", "limit": 1}
    headers = {"User-Agent": "osint-workspace-poc/0.1"}
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
        if data:
            return {"lat": float(data[0]["lat"]), "lng": float(data[0]["lon"])}
    except Exception:
        pass
    return None


async def reverse_geocode(lat: float, lng: float) -> dict:
    """Coordinates -> address via Nominatim (free, no key) with a fallback.

    Returns {"address", "city", "country"}.
    """
    url = "https://nominatim.openstreetmap.org/reverse"
    params = {
        "lat": lat,
        "lon": lng,
        "format": "jsonv2",
        "addressdetails": 1,
        "accept-language": "uk",
    }
    headers = {"User-Agent": "osint-workspace-poc/0.1"}
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
        address = data.get("address") or {}
        return {
            "address": data.get("display_name") or "",
            "city": address.get("city") or address.get("town") or address.get("village") or "",
            "country": address.get("country") or "",
        }
    except Exception:
        return {
            "address": f"~ ({lat:.4f}, {lng:.4f})",
            "city": "",
            "country": "",
        }
