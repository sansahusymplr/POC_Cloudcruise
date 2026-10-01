"""Turn a practitioner row + a CloudCruise workflow input_schema into the
`run_input_variables` payload.

Strategy:
- The practitioner table's columns are named to match schema keys 1:1. So the
  base pass is a name lookup against the practitioner's dict.
- Anything present in the schema but missing on the practitioner is left out
  (and reported back to the caller if it was in `required`).
- Values are coerced to strings because every field in the schema uses
  `type: "string"`.
- The function is schema-driven — new workflow with new fields works without
  code changes as long as the practitioner table has the columns.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class MappingResult:
    run_input_variables: dict[str, Any] = field(default_factory=dict)
    missing_required: list[str] = field(default_factory=list)
    unmapped_schema_keys: list[str] = field(default_factory=list)


def build_run_input(metadata: dict[str, Any], practitioner_row: dict[str, Any]) -> MappingResult:
    input_schema = (metadata or {}).get("input_schema") or {}
    properties: dict[str, Any] = input_schema.get("properties") or {}
    required: list[str] = list(input_schema.get("required") or [])

    result = MappingResult()

    for key, prop in properties.items():
        raw = practitioner_row.get(key)
        if raw is None or raw == "":
            result.unmapped_schema_keys.append(key)
            continue
        result.run_input_variables[key] = _coerce(raw, prop)

    for req in required:
        if req not in result.run_input_variables:
            result.missing_required.append(req)

    return result


def _coerce(value: Any, prop: dict[str, Any]) -> Any:
    """Every field in the metadata sample is `type: string`, but we still guard
    against future schemas that use number/boolean."""
    target = prop.get("type", "string")
    if target == "string":
        return str(value)
    if target in {"integer", "number"}:
        try:
            return int(value) if target == "integer" else float(value)
        except (TypeError, ValueError):
            return str(value)
    if target == "boolean":
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {"true", "yes", "1", "y"}
    return value
