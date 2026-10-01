from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import WorkflowMapping
from ..schemas import WorkflowMappingIn, WorkflowMappingOut

router = APIRouter(prefix="/api/mappings", tags=["mappings"])


@router.get("", response_model=list[WorkflowMappingOut])
def list_mappings(db: Session = Depends(get_db)):
    return db.query(WorkflowMapping).order_by(WorkflowMapping.id.desc()).all()


@router.post("", response_model=WorkflowMappingOut, status_code=201)
def create_mapping(payload: WorkflowMappingIn, db: Session = Depends(get_db)):
    existing = db.query(WorkflowMapping).filter(WorkflowMapping.target_url == payload.target_url).first()
    if existing:
        raise HTTPException(status_code=409, detail="target_url already mapped")
    mapping = WorkflowMapping(**payload.model_dump())
    db.add(mapping)
    db.commit()
    db.refresh(mapping)
    return mapping


@router.put("/{mapping_id}", response_model=WorkflowMappingOut)
def update_mapping(mapping_id: int, payload: WorkflowMappingIn, db: Session = Depends(get_db)):
    mapping = db.get(WorkflowMapping, mapping_id)
    if not mapping:
        raise HTTPException(status_code=404, detail="mapping not found")
    conflict = (
        db.query(WorkflowMapping)
        .filter(WorkflowMapping.target_url == payload.target_url, WorkflowMapping.id != mapping_id)
        .first()
    )
    if conflict:
        raise HTTPException(status_code=409, detail="target_url already mapped")
    mapping.name = payload.name
    mapping.target_url = payload.target_url
    mapping.workflow_id = payload.workflow_id
    db.commit()
    db.refresh(mapping)
    return mapping


@router.delete("/{mapping_id}", status_code=204)
def delete_mapping(mapping_id: int, db: Session = Depends(get_db)):
    mapping = db.get(WorkflowMapping, mapping_id)
    if not mapping:
        raise HTTPException(status_code=404, detail="mapping not found")
    db.delete(mapping)
    db.commit()
