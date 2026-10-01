from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class WorkflowMapping(Base):
    """Maps a target URL (the site to autofill) to a CloudCruise workflow_id."""

    __tablename__ = "workflow_mappings"
    __table_args__ = (UniqueConstraint("target_url", name="uq_workflow_mappings_target_url"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    target_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    workflow_id: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Practitioner(Base):
    """Practitioner record. Column names deliberately mirror the CloudCruise
    input_schema keys so the mapper can pick fields dynamically."""

    __tablename__ = "practitioners"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Contacts
    credentialing_contact_name: Mapped[str | None] = mapped_column(String(255))
    credentialing_contact_phone: Mapped[str | None] = mapped_column(String(64))
    credentialing_contact_email: Mapped[str | None] = mapped_column(String(255))
    practice_contact_name: Mapped[str | None] = mapped_column(String(255))
    practice_contact_email: Mapped[str | None] = mapped_column(String(255))

    # Provider identity
    first_name: Mapped[str | None] = mapped_column(String(128))
    middle_name: Mapped[str | None] = mapped_column(String(128))
    last_name: Mapped[str | None] = mapped_column(String(128))
    suffix_name: Mapped[str | None] = mapped_column(String(32))
    social_security_number: Mapped[str | None] = mapped_column(String(32))
    birth_date: Mapped[str | None] = mapped_column(String(32))
    gender: Mapped[str | None] = mapped_column(String(16))

    # Licensure
    license_type: Mapped[str | None] = mapped_column(String(64))
    license_state: Mapped[str | None] = mapped_column(String(64))
    license_number: Mapped[str | None] = mapped_column(String(64))
    license_expiration: Mapped[str | None] = mapped_column(String(32))
    provider_start_date: Mapped[str | None] = mapped_column(String(32))

    # Supervising
    supervising_physician_name: Mapped[str | None] = mapped_column(String(255))
    supervising_physician_specialty: Mapped[str | None] = mapped_column(String(255))
    cultural_competence_training: Mapped[str | None] = mapped_column(String(8))

    # Practice
    practice_website: Mapped[str | None] = mapped_column(String(255))
    practice_email: Mapped[str | None] = mapped_column(String(255))

    # Primary location
    primary_address_type: Mapped[str | None] = mapped_column(String(64))
    primary_group_name: Mapped[str | None] = mapped_column(String(255))
    primary_address_line1: Mapped[str | None] = mapped_column(String(255))
    primary_address_line2: Mapped[str | None] = mapped_column(String(255))
    primary_city: Mapped[str | None] = mapped_column(String(128))
    primary_state: Mapped[str | None] = mapped_column(String(64))
    primary_zip: Mapped[str | None] = mapped_column(String(16))
    primary_phone: Mapped[str | None] = mapped_column(String(64))
    primary_fax: Mapped[str | None] = mapped_column(String(64))
    primary_group_npi: Mapped[str | None] = mapped_column(String(32))
    primary_specialty: Mapped[str | None] = mapped_column(String(128))
    primary_fte_requirement: Mapped[str | None] = mapped_column(String(8))
    primary_epsdt: Mapped[str | None] = mapped_column(String(8))
    primary_asl: Mapped[str | None] = mapped_column(String(8))
    primary_khie: Mapped[str | None] = mapped_column(String(8))
    primary_age_range: Mapped[str | None] = mapped_column(String(64))
    primary_hours_monday: Mapped[str | None] = mapped_column(String(64))
    primary_hours_tuesday: Mapped[str | None] = mapped_column(String(64))
    primary_hours_wednesday: Mapped[str | None] = mapped_column(String(64))
    primary_hours_thursday: Mapped[str | None] = mapped_column(String(64))
    primary_hours_friday: Mapped[str | None] = mapped_column(String(64))
    primary_hours_saturday: Mapped[str | None] = mapped_column(String(64))
    primary_hours_sunday: Mapped[str | None] = mapped_column(String(64))
    primary_lab_services: Mapped[str | None] = mapped_column(String(8))
    primary_handicap_accessibility: Mapped[str | None] = mapped_column(String(8))
    primary_tdd_capability: Mapped[str | None] = mapped_column(String(8))
    primary_bus_route: Mapped[str | None] = mapped_column(String(8))
    primary_locum_tenens: Mapped[str | None] = mapped_column(String(8))
    primary_accepting_new_patients: Mapped[str | None] = mapped_column(String(128))
    primary_pcp_or_specialist: Mapped[str | None] = mapped_column(String(32))
    primary_scope_of_practice: Mapped[str | None] = mapped_column(String(64))

    # CLIA
    clia_number: Mapped[str | None] = mapped_column(String(32))
    clia_expiration: Mapped[str | None] = mapped_column(String(32))

    # Flags
    provider_bills_dme: Mapped[str | None] = mapped_column(String(16))
    telehealth_services: Mapped[str | None] = mapped_column(String(8))

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class AutofillSession(Base):
    """History of every autofill attempt."""

    __tablename__ = "autofill_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    practitioner_id: Mapped[int] = mapped_column(Integer, nullable=False)
    workflow_id: Mapped[str] = mapped_column(String(128), nullable=False)
    target_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    cc_session_id: Mapped[str | None] = mapped_column(String(255))
    cc_session_url: Mapped[str | None] = mapped_column(String(1024))
    status: Mapped[str] = mapped_column(String(64), nullable=False)  # success | failed
    error_message: Mapped[str | None] = mapped_column(Text)
    request_payload: Mapped[str | None] = mapped_column(Text)
    response_payload: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
