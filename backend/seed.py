"""Populate the SQLite DB with demo data:
- one workflow mapping (using the workflow_id from the task brief)
- 25 sample practitioners

Run with:  python -m backend.seed
"""

from __future__ import annotations

import random

from .database import Base, SessionLocal, engine
from .models import Practitioner, WorkflowMapping

SAMPLE_WORKFLOW_ID = "2e8bfa9c-aa3b-42e5-9c16-a63ec4eb46e7"

FIRST_NAMES = ["John", "Emily", "Michael", "Sarah", "David", "Jessica", "Robert", "Linda",
               "William", "Karen", "James", "Patricia", "Chris", "Barbara", "Daniel", "Nancy",
               "Matthew", "Ashley", "Kevin", "Amanda", "Ryan", "Melissa", "Brian", "Rachel", "Andrew"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
              "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
              "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
              "White", "Harris"]
LICENSE_TYPES = ["MD", "DO", "NP", "PA"]
STATES = [("KY", "Kentucky"), ("OH", "Ohio"), ("TN", "Tennessee"), ("IN", "Indiana"), ("WV", "West Virginia")]
CITIES = ["Louisville", "Lexington", "Bowling Green", "Owensboro", "Covington"]
SPECIALTIES = ["Family Medicine", "Internal Medicine", "Pediatrics", "OB/GYN", "Cardiology", "Obstetrics"]
GROUP_NAMES = ["Downtown OB Group", "Bluegrass Family Clinic", "Riverside Medical", "Cardinal Health Partners", "Heartland Pediatrics"]


def _make_practitioner(i: int) -> Practitioner:
    rnd = random.Random(i)
    first = rnd.choice(FIRST_NAMES)
    last = rnd.choice(LAST_NAMES)
    state_code, state_full = rnd.choice(STATES)
    license_type = rnd.choice(LICENSE_TYPES)
    specialty = rnd.choice(SPECIALTIES)
    group = rnd.choice(GROUP_NAMES)
    city = rnd.choice(CITIES)
    zip_code = f"402{rnd.randint(10, 99)}"
    year = rnd.randint(1965, 1990)
    return Practitioner(
        credentialing_contact_name=f"Jane Admin {i}",
        credentialing_contact_phone=f"502-555-{1000+i:04d}",
        credentialing_contact_email=f"jane{i}@clinic.com",
        practice_contact_name=f"Bob Office {i}",
        practice_contact_email=f"bob{i}@clinic.com",
        first_name=first,
        middle_name=rnd.choice(["A", "B", "C", "D", "E", ""]) or None,
        last_name=last,
        suffix_name=license_type,
        social_security_number=f"{rnd.randint(100,999)}-{rnd.randint(10,99)}-{rnd.randint(1000,9999)}",
        birth_date=f"{rnd.randint(1,12):02d}/{rnd.randint(1,28):02d}/{year}",
        gender=rnd.choice(["Male", "Female"]),
        license_type=license_type,
        license_state=state_code,
        license_number=f"{rnd.randint(10000, 99999)}",
        license_expiration="12/31/2026",
        provider_start_date="01/01/2025",
        supervising_physician_name=f"Dr. {rnd.choice(FIRST_NAMES)} {rnd.choice(LAST_NAMES)}",
        supervising_physician_specialty=rnd.choice(SPECIALTIES),
        cultural_competence_training="Yes",
        practice_website="https://clinic.example.com",
        practice_email=f"info{i}@clinic.com",
        primary_address_type="Primary Office",
        primary_group_name=group,
        primary_address_line1=f"{rnd.randint(100, 999)} Main St",
        primary_address_line2=None,
        primary_city=city,
        primary_state=state_full,
        primary_zip=zip_code,
        primary_phone=f"502-555-{2000+i:04d}",
        primary_fax=f"502-555-{3000+i:04d}",
        primary_group_npi=f"{rnd.randint(1_000_000_000, 9_999_999_999)}",
        primary_specialty=specialty,
        primary_fte_requirement="Yes",
        primary_epsdt="No",
        primary_asl="No",
        primary_khie="No",
        primary_age_range="18-65",
        primary_hours_monday="9am-5pm",
        primary_hours_tuesday="9am-5pm",
        primary_hours_wednesday="9am-5pm",
        primary_hours_thursday="9am-5pm",
        primary_hours_friday="9am-5pm",
        primary_hours_saturday="Closed",
        primary_hours_sunday="Closed",
        primary_lab_services="No",
        primary_handicap_accessibility="Yes",
        primary_tdd_capability="No",
        primary_bus_route="Yes",
        primary_locum_tenens="No",
        primary_accepting_new_patients="Yes; Provider accepts patient appointments at this location.",
        primary_pcp_or_specialist=rnd.choice(["PCP", "Specialist"]),
        primary_scope_of_practice="Specialty Care" if specialty != "Family Medicine" else "Primary Care",
        provider_bills_dme="No",
        telehealth_services="Yes",
    )


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if not db.query(WorkflowMapping).first():
            db.add(WorkflowMapping(
                name="Kentucky Medicaid Provider Enrollment",
                target_url="https://kymedicaid.example.com/enroll",
                workflow_id=SAMPLE_WORKFLOW_ID,
            ))
        if not db.query(Practitioner).first():
            for i in range(1, 26):
                db.add(_make_practitioner(i))
        db.commit()
        print("Seed complete.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
