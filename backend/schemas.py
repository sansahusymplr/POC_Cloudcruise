from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class WorkflowMappingIn(BaseModel):
    name: str = Field(min_length=1)
    target_url: str = Field(min_length=1)
    workflow_id: str = Field(min_length=1)


class WorkflowMappingOut(WorkflowMappingIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


class PractitionerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    first_name: str | None = None
    last_name: str | None = None
    license_type: str | None = None
    license_state: str | None = None
    license_number: str | None = None
    primary_group_name: str | None = None
    primary_city: str | None = None
    primary_state: str | None = None
    primary_specialty: str | None = None


class PractitionerListOut(BaseModel):
    items: list[PractitionerOut]
    total: int
    page: int
    page_size: int


class AutofillRequest(BaseModel):
    practitioner_id: int
    target_url: str


class AutofillResponse(BaseModel):
    status: str
    workflow_id: str
    target_url: str
    cc_session_id: str | None = None
    cc_session_url: str | None = None
    missing_required: list[str] = []
    unmapped_schema_keys: list[str] = []
    run_input_variables: dict[str, Any] = {}
    error_message: str | None = None


class SessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    practitioner_id: int
    workflow_id: str
    target_url: str
    cc_session_id: str | None
    cc_session_url: str | None
    status: str
    error_message: str | None
    created_at: datetime
