"""Thin wrapper around the two CloudCruise endpoints we call.

The cc-key is only read here. Callers pass just the workflow_id and payload.
"""

from __future__ import annotations

from typing import Any

import httpx

from .config import settings


class CloudCruiseError(RuntimeError):
    def __init__(self, message: str, status_code: int | None = None, body: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.body = body


def _headers() -> dict[str, str]:
    if not settings.cc_key:
        raise CloudCruiseError("CC_KEY is not configured. Set it in .env before making live calls.")
    return {"cc-key": settings.cc_key, "Content-Type": "application/json"}


async def get_workflow_metadata(workflow_id: str) -> dict[str, Any]:
    url = f"{settings.cc_base_url.rstrip('/')}/workflows/{workflow_id}/metadata"
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url, headers=_headers())
    if resp.status_code >= 400:
        raise CloudCruiseError(
            f"metadata request failed ({resp.status_code})", resp.status_code, _safe_json(resp)
        )
    return resp.json()


async def run_workflow(
    workflow_id: str,
    run_input_variables: dict[str, Any],
    *,
    dry_run: bool | None = None,
) -> dict[str, Any]:
    """POST /run with a normalized payload. Only fields the caller cares about
    are populated; the rest of CloudCruise's optional fields are omitted."""

    payload: dict[str, Any] = {
        "workflow_id": workflow_id,
        "run_input_variables": run_input_variables,
        "dry_run": {"enabled": settings.cc_dry_run if dry_run is None else dry_run},
        "notifications": {"enabled": True},
        "priority_level": "LOW",
    }
    url = f"{settings.cc_base_url.rstrip('/')}/run"
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(url, headers=_headers(), json=payload)
    if resp.status_code >= 400:
        raise CloudCruiseError(
            f"run request failed ({resp.status_code})", resp.status_code, _safe_json(resp)
        )
    return resp.json()


def _safe_json(resp: httpx.Response) -> Any:
    try:
        return resp.json()
    except Exception:
        return resp.text
