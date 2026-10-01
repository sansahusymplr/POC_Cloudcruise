import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import inspect
from sqlalchemy.orm import Session

from ..cloudcruise import CloudCruiseError, get_workflow_metadata, run_workflow
from ..database import get_db
from ..mapper import build_run_input
from ..models import AutofillSession, Practitioner, WorkflowMapping
from ..schemas import AutofillRequest, AutofillResponse

router = APIRouter(prefix="/api/autofill", tags=["autofill"])


def _practitioner_dict(p: Practitioner) -> dict:
    return {c.key: getattr(p, c.key) for c in inspect(Practitioner).mapper.column_attrs}


def _extract_session(response: dict) -> tuple[str | None, str | None]:
    """CloudCruise's /run response shape isn't documented in the sample, so we
    look for likely id/url fields without breaking if they're absent."""
    session_id = (
        response.get("session_id")
        or response.get("run_id")
        or response.get("id")
        or (response.get("run") or {}).get("id")
    )
    session_url = (
        response.get("session_url")
        or response.get("run_url")
        or response.get("url")
        or (response.get("run") or {}).get("url")
    )
    return session_id, session_url


@router.post("", response_model=AutofillResponse)
async def trigger_autofill(payload: AutofillRequest, db: Session = Depends(get_db)):
    mapping = db.query(WorkflowMapping).filter(WorkflowMapping.target_url == payload.target_url).first()
    if not mapping:
        raise HTTPException(status_code=404, detail=f"no workflow mapping for target_url {payload.target_url!r}")

    practitioner = db.get(Practitioner, payload.practitioner_id)
    if not practitioner:
        raise HTTPException(status_code=404, detail="practitioner not found")

    workflow_id = mapping.workflow_id
    prac_row = _practitioner_dict(practitioner)

    try:
        metadata = await get_workflow_metadata(workflow_id)
    except CloudCruiseError as e:
        _record_session(db, payload, workflow_id, status="failed", error=f"metadata: {e}")
        raise HTTPException(status_code=502, detail=f"CloudCruise metadata call failed: {e}")

    mapped = build_run_input(metadata, prac_row)

    if mapped.missing_required:
        session = _record_session(
            db,
            payload,
            workflow_id,
            status="failed",
            error=f"missing required fields: {', '.join(mapped.missing_required)}",
            request_payload=mapped.run_input_variables,
        )
        return AutofillResponse(
            status=session.status,
            workflow_id=workflow_id,
            target_url=payload.target_url,
            missing_required=mapped.missing_required,
            unmapped_schema_keys=mapped.unmapped_schema_keys,
            run_input_variables=mapped.run_input_variables,
            error_message=session.error_message,
        )

    try:
        response = await run_workflow(workflow_id, mapped.run_input_variables)
    except CloudCruiseError as e:
        session = _record_session(
            db,
            payload,
            workflow_id,
            status="failed",
            error=f"run: {e}",
            request_payload=mapped.run_input_variables,
            response_payload=e.body,
        )
        return AutofillResponse(
            status=session.status,
            workflow_id=workflow_id,
            target_url=payload.target_url,
            missing_required=mapped.missing_required,
            unmapped_schema_keys=mapped.unmapped_schema_keys,
            run_input_variables=mapped.run_input_variables,
            error_message=session.error_message,
        )

    cc_session_id, cc_session_url = _extract_session(response)
    session = _record_session(
        db,
        payload,
        workflow_id,
        status="success",
        cc_session_id=cc_session_id,
        cc_session_url=cc_session_url,
        request_payload=mapped.run_input_variables,
        response_payload=response,
    )

    return AutofillResponse(
        status=session.status,
        workflow_id=workflow_id,
        target_url=payload.target_url,
        cc_session_id=session.cc_session_id,
        cc_session_url=session.cc_session_url,
        missing_required=mapped.missing_required,
        unmapped_schema_keys=mapped.unmapped_schema_keys,
        run_input_variables=mapped.run_input_variables,
    )


def _record_session(
    db: Session,
    payload: AutofillRequest,
    workflow_id: str,
    *,
    status: str,
    error: str | None = None,
    cc_session_id: str | None = None,
    cc_session_url: str | None = None,
    request_payload=None,
    response_payload=None,
) -> AutofillSession:
    row = AutofillSession(
        practitioner_id=payload.practitioner_id,
        workflow_id=workflow_id,
        target_url=payload.target_url,
        cc_session_id=cc_session_id,
        cc_session_url=cc_session_url,
        status=status,
        error_message=error,
        request_payload=json.dumps(request_payload, default=str) if request_payload is not None else None,
        response_payload=json.dumps(response_payload, default=str) if response_payload is not None else None,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
