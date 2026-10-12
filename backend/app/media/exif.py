import hashlib
from io import BytesIO

from PIL import ExifTags, Image


def compute_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _to_decimal(value, ref: str) -> float | None:
    try:
        d = float(value[0]) + float(value[1]) / 60.0 + float(value[2]) / 3600.0
        if ref in ("S", "W"):
            d = -d
        return round(d, 6)
    except (TypeError, IndexError, ValueError, ZeroDivisionError):
        return None


def extract_image_info(data: bytes) -> dict:
    """Extract metadata + GPS from an image (real EXIF parsing via Pillow).

    Returns a dict with sha256, resolution, gps, datetime, device, exif.
    Never raises — degrades gracefully to empty fields.
    """
    info: dict = {
        "sha256": compute_sha256(data),
        "width": 0,
        "height": 0,
        "gps": None,
        "datetime": "",
        "device": "",
        "exif": {},
    }

    try:
        img = Image.open(BytesIO(data))
        info["width"], info["height"] = img.size

        exif = img.getexif()
        if not exif:
            return info

        info["exif"] = {
            ExifTags.TAGS.get(k, k): _stringify(v) for k, v in exif.items()
        }

        # GPS IFD (tag 0x8825)
        gps_ifd = exif.get_ifd(0x8825)
        if gps_ifd:
            gps = {ExifTags.GPSTAGS.get(k, k): v for k, v in gps_ifd.items()}
            lat = _to_decimal(gps.get("GPSLatitude"), str(gps.get("GPSLatitudeRef", "")))
            lng = _to_decimal(gps.get("GPSLongitude"), str(gps.get("GPSLongitudeRef", "")))
            if lat is not None and lng is not None:
                info["gps"] = {"lat": lat, "lng": lng}

        dt = exif.get(0x0132)  # DateTimeOriginal
        if dt:
            info["datetime"] = str(dt)

        make = exif.get(0x010F)
        model = exif.get(0x0110)
        if make or model:
            info["device"] = f"{make or ''} {model or ''}".strip()
    except Exception:
        pass

    return info


def _stringify(value) -> str:
    if isinstance(value, (bytes, bytearray)):
        return value.decode("utf-8", errors="replace")
    return str(value)
