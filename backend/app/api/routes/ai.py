from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...ai.providers import RESERVED_NAMES, available as available_providers
from ...database import get_db
from ...models.provider_config import ProviderConfig
from ...schemas.provider import ProviderCreate, ProviderRead

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.get("/providers")
def list_providers(db: Session = Depends(get_db)):
    return {"providers": available_providers(db)}


@router.post("/providers", response_model=ProviderRead)
def create_provider(body: ProviderCreate, db: Session = Depends(get_db)):
    name = body.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Назва обов'язкова")
    if name.lower() in RESERVED_NAMES:
        raise HTTPException(status_code=400, detail="Це зарезервована назва")
    if db.query(ProviderConfig).filter(ProviderConfig.name == name).first():
        raise HTTPException(status_code=409, detail="Модель із такою назвою вже існує")

    kind = body.kind if body.kind in ("openai", "ollama", "claude") else "openai"
    cfg = ProviderConfig(
        name=name,
        kind=kind,
        base_url=body.base_url.strip(),
        api_key=body.api_key.strip(),
        model=body.model.strip(),
    )
    db.add(cfg)
    db.commit()
    db.refresh(cfg)
    return _to_read(cfg)


@router.delete("/providers/{provider_id}")
def delete_provider(provider_id: int, db: Session = Depends(get_db)):
    cfg = db.get(ProviderConfig, provider_id)
    if cfg is None:
        raise HTTPException(status_code=404, detail="Модель не знайдено")
    db.delete(cfg)
    db.commit()
    return {"ok": True}


def _to_read(cfg: ProviderConfig) -> ProviderRead:
    return ProviderRead(
        id=cfg.id,
        name=cfg.name,
        kind=cfg.kind,
        model=cfg.model,
        configured=True,
    )
