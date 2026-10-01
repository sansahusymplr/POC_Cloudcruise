from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import AutofillSession
from ..schemas import SessionOut

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.get("", response_model=list[SessionOut])
def list_sessions(
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return (
        db.query(AutofillSession)
        .order_by(AutofillSession.id.desc())
        .limit(limit)
        .all()
    )
