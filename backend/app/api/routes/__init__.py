from .ai import router as ai_router
from .analyze import router as analyze_router
from .entities import router as entities_router
from .geocode import router as geocode_router
from .images import router as images_router
from .search import router as search_router
from .workspaces import router as workspaces_router

__all__ = [
    "ai_router",
    "analyze_router",
    "entities_router",
    "geocode_router",
    "images_router",
    "search_router",
    "workspaces_router",
]
