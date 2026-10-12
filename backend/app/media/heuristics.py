from datetime import datetime, timedelta


def check_metadata(info: dict) -> list[dict]:
    """Non-AI consistency checks over image metadata.

    Returns a list of {"level": "error"|"warn", "text": str}. These run
    without any model and catch obvious manipulation / stripped metadata.
    """
    findings: list[dict] = []

    gps = info.get("gps")
    if gps is None:
        findings.append({"level": "warn", "text": "GPS у метаданих відсутній"})
    else:
        lat, lng = gps["lat"], gps["lng"]
        if abs(lat) < 1e-9 and abs(lng) < 1e-9:
            findings.append(
                {"level": "error", "text": "GPS = (0, 0) — ймовірно заглушка або видалений геотег"}
            )
        elif not (-90 <= lat <= 90 and -180 <= lng <= 180):
            findings.append({"level": "error", "text": "Координати поза допустимими межами"})

    dt = info.get("datetime")
    if dt:
        try:
            parsed = datetime.strptime(str(dt)[:19], "%Y:%m:%d %H:%M:%S")
            if parsed > datetime.now() + timedelta(days=1):
                findings.append({"level": "error", "text": "Дата зйомки в майбутньому — підозріло"})
        except ValueError:
            findings.append({"level": "warn", "text": "Незрозумілий формат дати зйомки"})
    else:
        findings.append({"level": "warn", "text": "Відсутня дата зйомки"})

    if not info.get("device"):
        findings.append(
            {"level": "warn", "text": "Відсутня інформація про пристрій (можливий скріншот/повторна обробка)"}
        )

    return findings
