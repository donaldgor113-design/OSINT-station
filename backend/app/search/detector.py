import re

_IPV4 = re.compile(r"^(\d{1,3}\.){3}\d{1,3}$")
_DOMAIN = re.compile(r"^([a-z0-9-]+\.)+[a-z]{2,}$", re.I)
_EDRPOU = re.compile(r"^\d{8}$")
_IPN = re.compile(r"^\d{10}$")
_COORDS = re.compile(r"^-?\d{1,3}\.\d+,\s*-?\d{1,3}\.\d+$")


def detect_query_type(query: str) -> str:
    """Тип даних у запиті (не намір!)."""
    q = query.strip()
    if _IPV4.match(q):
        return "ip"
    if _COORDS.match(q):
        return "location"
    if _EDRPOU.match(q):
        return "company_edrpou"
    if _IPN.match(q):
        return "person_ipn"
    if _DOMAIN.match(q):
        return "domain"
    if q.startswith("@"):
        return "handle"
    return "text"


def detect_intent(query: str, query_type: str) -> str:
    """
    Що користувач насправді хоче знайти.
    Використовується для вибору інтентів у dorksmith та для пріоритезації.
    """
    q_lower = query.lower()

    intent_map = {
        "ip": "ip-recon",
        "domain": "domain-recon",
        "company_edrpou": "company-profile",
        "person_ipn": "person-profile",
        "handle": "social-profile",
        "location": "geo-context",
        "text": "general-discovery",
    }

    # Додаткові евристики для текстових запитів
    if query_type == "text":
        if any(w in q_lower for w in ("тов", "фоп", "пп ", "єдрпоу")):
            return "company-profile"
        if any(w in q_lower for w in ("телефон", "email", "пошта", "@")):
            return "contact-discovery"
        if any(w in q_lower for w in ("документ", "pdf", "звіт", "наказ")):
            return "public-documents"
        if any(w in q_lower for w in ("плів", "фото", "зображення")):
            return "media-discovery"

    return intent_map.get(query_type, "general-discovery")
