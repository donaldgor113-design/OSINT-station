from datetime import datetime, timezone
from statistics import mean


def detect_anomalies(entities: list[dict]) -> list[str]:
    """Heuristic anomaly detection over compact entities.

    Honest, rule-based checks (no ML): stale observations and geographic
    outliers among location entities. Returns human-readable flags.
    """
    anomalies: list[str] = []
    if not entities:
        return anomalies

    now = datetime.now(timezone.utc)

    for e in entities:
        obs = e.get("observed_at")
        if obs:
            try:
                dt = datetime.fromisoformat(str(obs).replace("Z", "+00:00"))
                age_days = (now - dt).days
                if age_days > 365:
                    anomalies.append(f"{e.get('name')} — дані застарілі ({age_days} дн.)")
            except ValueError:
                pass

    locs = [e for e in entities if len(e.get("coordinates") or []) == 2]
    if len(locs) >= 3:
        cx = mean(e["coordinates"][0] for e in locs)
        cy = mean(e["coordinates"][1] for e in locs)
        distances = [
            ((e["coordinates"][0] - cx) ** 2 + (e["coordinates"][1] - cy) ** 2) ** 0.5
            for e in locs
        ]
        avg = mean(distances)
        if avg > 0:
            for e, d in zip(locs, distances):
                if d > avg * 2:
                    anomalies.append(
                        f"{e.get('name')} — географічно випадає з кластера інших локацій"
                    )

    return anomalies
