from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import inspect
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Practitioner
from ..schemas import PractitionerListOut, PractitionerOut

router = APIRouter(prefix="/api/practitioners", tags=["practitioners"])


@router.get("", response_model=PractitionerListOut)
def list_practitioners(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    total = db.query(Practitioner).count()
    items = (
        db.query(Practitioner)
        .order_by(Practitioner.id.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return PractitionerListOut(
        items=[PractitionerOut.model_validate(p) for p in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{practitioner_id}")
def get_practitioner(practitioner_id: int, db: Session = Depends(get_db)):
    """Full record as a plain dict — this is what the mapper consumes."""
    p = db.get(Practitioner, practitioner_id)
    if not p:
        raise HTTPException(status_code=404, detail="practitioner not found")
    columns = [c.key for c in inspect(Practitioner).mapper.column_attrs]
    return {col: getattr(p, col) for col in columns}
