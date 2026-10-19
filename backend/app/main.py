from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import (
    ai_router,
    analyze_router,
    entities_router,
    geocode_router,
    images_router,
    search_router,
    workspaces_router,
)
from .config import get_settings
from .database import Base, engine
from .search.cache import SearchCache

settings = get_settings()


def create_app() -> FastAPI:
    Base.metadata.create_all(bind=engine)

    app = FastAPI(title="OSINT Workspace API", version="0.1.0")

    # Спільний кеш пошуку — живе довше за один HTTP-запит.
    app.state.search_cache = SearchCache(settings.redis_url or None)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(workspaces_router)
    app.include_router(search_router)
    app.include_router(entities_router)
    app.include_router(analyze_router)
    app.include_router(geocode_router)
    app.include_router(images_router)
    app.include_router(ai_router)

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    return app


app = create_app()
