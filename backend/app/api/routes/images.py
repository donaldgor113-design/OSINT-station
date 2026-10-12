from fastapi import APIRouter, File, UploadFile

from ...ai.vision import describe_image, verify_location
from ...media.exif import extract_image_info
from ...media.geocode import reverse_geocode
from ...media.heuristics import check_metadata

router = APIRouter(prefix="/api/images", tags=["images"])


@router.post("/analyze")
async def analyze_image(file: UploadFile = File(...)):
    """Analyze an uploaded image: EXIF/GPS + reverse geocode + description + checks."""
    data = await file.read()
    mime = file.content_type or "image/jpeg"
    info = extract_image_info(data)

    address = None
    if info["gps"]:
        address = await reverse_geocode(info["gps"]["lat"], info["gps"]["lng"])

    description = await describe_image(data, info, mime)

    # Non-AI checks (always run) + optional vision verification.
    checks = check_metadata(info)
    vision = None
    if info["gps"]:
        country = (address or {}).get("country", "")
        vision = await verify_location(data, country, mime)

    consistency = _compute_consistency(checks, vision)

    return {
        "sha256": info["sha256"],
        "width": info["width"],
        "height": info["height"],
        "gps": info["gps"],
        "datetime": info["datetime"],
        "device": info["device"],
        "address": address,
        "ai_description": description,
        "checks": checks,
        "vision": vision,
        "consistency": consistency,
    }


def _compute_consistency(checks: list[dict], vision: dict | None) -> dict:
    errors = [c["text"] for c in checks if c["level"] == "error"]

    if vision and vision["status"] == "mismatch":
        return {"status": "mismatch", "detail": vision["detail"]}
    if errors:
        return {
            "status": "mismatch",
            "detail": "Підозрілі ознаки: " + "; ".join(errors),
        }
    if vision and vision["status"] == "ok":
        return {"status": "ok", "detail": "Метадані узгоджені та візуально підтверджені"}
    return {
        "status": "unchecked",
        "detail": "Явних розбіжностей не виявлено (візуальну перевірку не виконано)",
    }
