from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...database import get_db
from ...models.universal_entity import UniversalEntity
from ...models.workspace import Workspace
from ...schemas.workspace import WorkspaceCreate, WorkspaceRead

router = APIRouter(prefix="/api/workspaces", tags=["workspaces"])


@router.get("", response_model=list[WorkspaceRead])
def list_workspaces(db: Session = Depends(get_db)):
    return db.query(Workspace).order_by(Workspace.id).all()


@router.post("", response_model=WorkspaceRead)
def create_workspace(body: WorkspaceCreate, db: Session = Depends(get_db)):
    name = body.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Name is required")
    if db.query(Workspace).filter(Workspace.name == name).first():
        raise HTTPException(status_code=409, detail="Дослідження з такою назвою вже існує")
    workspace = Workspace(name=name, description=body.description.strip())
    db.add(workspace)
    db.commit()
    db.refresh(workspace)
    return workspace


@router.get("/{workspace_id}", response_model=WorkspaceRead)
def get_workspace(workspace_id: int, db: Session = Depends(get_db)):
    workspace = db.get(Workspace, workspace_id)
    if workspace is None:
        raise HTTPException(status_code=404, detail="Дослідження не знайдено")
    return workspace


@router.delete("/{workspace_id}")
def delete_workspace(workspace_id: int, db: Session = Depends(get_db)):
    workspace = db.get(Workspace, workspace_id)
    if workspace is None:
        raise HTTPException(status_code=404, detail="Дослідження не знайдено")
    db.query(UniversalEntity).filter(
        UniversalEntity.workspace_id == workspace_id
    ).delete()
    db.delete(workspace)
    db.commit()
    return {"ok": True}
