from .providers import get as _get


def get_ai_provider():
    """Auto-select an AI provider based on settings (backward-compatible helper)."""
    return _get(None, None)
