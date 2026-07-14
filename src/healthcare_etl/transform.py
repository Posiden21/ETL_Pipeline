"""Transform and validate healthcare encounter records."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation


DATE_FORMAT = "%Y-%m-%d"


@dataclass(frozen=True)
class TransformResult:
    # The transform step returns load-ready records plus rows that failed validation.
    patients: list[dict[str, object]]
    encounters: list[dict[str, object]]
    rejected_rows: list[dict[str, object]]


def transform_encounters(rows: list[dict[str, str]], as_of: date | None = None) -> TransformResult:
    """Validate raw records and produce patient, encounter, and rejection tables."""
    as_of = as_of or date.today()
    # Patients are keyed by ID because one patient can appear across many encounters.
    patients_by_id: dict[str, dict[str, object]] = {}
    encounters: list[dict[str, object]] = []
    rejected_rows: list[dict[str, object]] = []
    seen_encounter_ids: set[str] = set()

    for row_number, row in enumerate(rows, start=2):
        # CSV row numbers start at 2 because row 1 contains headers.
        errors = _validate_row(row, seen_encounter_ids)
        if errors:
            rejected_rows.append(
                {
                    "row_number": row_number,
                    "patient_id": row.get("patient_id", ""),
                    "encounter_id": row.get("encounter_id", ""),
                    "reason": "; ".join(errors),
                }
            )
            continue

        patient_id = row["patient_id"].strip()
        encounter_id = row["encounter_id"].strip()
        seen_encounter_ids.add(encounter_id)

        birth_date = _parse_date(row["date_of_birth"])
        admit_date = _parse_date(row["admit_date"])
        discharge_date = _parse_date(row["discharge_date"])
        total_cost = Decimal(row["total_cost"])
        readmitted = _parse_bool(row["readmitted_30_days"])
        age = _calculate_age(birth_date, as_of)

        # Normalize presentation fields once so all outputs share the same formatting.
        encounters.append(
            {
                "encounter_id": encounter_id,
                "patient_id": patient_id,
                "admit_date": admit_date.isoformat(),
                "discharge_date": discharge_date.isoformat(),
                "length_of_stay_days": (discharge_date - admit_date).days,
                "department": row["department"].strip().title(),
                "diagnosis": row["diagnosis"].strip(),
                "procedure_code": row["procedure_code"].strip().upper(),
                "total_cost": float(total_cost),
                "readmitted_30_days": readmitted,
            }
        )

        current_patient = patients_by_id.get(patient_id)
        risk_tier = _risk_tier(age=age, total_cost=total_cost, readmitted=readmitted)
        # Keep the highest observed risk tier when multiple encounters share a patient.
        if current_patient is None or _risk_rank(risk_tier) > _risk_rank(str(current_patient["risk_tier"])):
            patients_by_id[patient_id] = {
                "patient_id": patient_id,
                "first_name": row["first_name"].strip().title(),
                "last_name": row["last_name"].strip().title(),
                "date_of_birth": birth_date.isoformat(),
                "age": age,
                "gender": row["gender"].strip().upper(),
                "risk_tier": risk_tier,
            }

    return TransformResult(
        patients=sorted(patients_by_id.values(), key=lambda record: str(record["patient_id"])),
        encounters=sorted(encounters, key=lambda record: str(record["encounter_id"])),
        rejected_rows=rejected_rows,
    )


def _validate_row(row: dict[str, str], seen_encounter_ids: set[str]) -> list[str]:
    # Collect every row-level validation issue so rejected output is actionable.
    errors: list[str] = []
    required_fields = [
        "patient_id",
        "first_name",
        "last_name",
        "date_of_birth",
        "encounter_id",
        "admit_date",
        "discharge_date",
        "department",
        "diagnosis",
        "procedure_code",
        "total_cost",
    ]

    for field in required_fields:
        if not row.get(field, "").strip():
            errors.append(f"missing {field}")

    if errors:
        # Skip type/date checks until required values are present.
        return errors

    encounter_id = row["encounter_id"].strip()
    if encounter_id in seen_encounter_ids:
        errors.append("duplicate encounter_id")

    try:
        birth_date = _parse_date(row["date_of_birth"])
        admit_date = _parse_date(row["admit_date"])
        discharge_date = _parse_date(row["discharge_date"])
    except ValueError as exc:
        errors.append(str(exc))
    else:
        if birth_date >= admit_date:
            errors.append("date_of_birth must be before admit_date")
        if discharge_date < admit_date:
            errors.append("discharge_date must be on or after admit_date")

    try:
        total_cost = Decimal(row["total_cost"])
    except InvalidOperation:
        errors.append("total_cost must be numeric")
    else:
        if total_cost < 0:
            errors.append("total_cost cannot be negative")

    try:
        _parse_bool(row.get("readmitted_30_days", "false"))
    except ValueError as exc:
        errors.append(str(exc))

    return errors


def _parse_date(value: str) -> date:
    # Store and validate dates in a single ISO-like format throughout the pipeline.
    try:
        return datetime.strptime(value.strip(), DATE_FORMAT).date()
    except ValueError as exc:
        raise ValueError(f"date must use {DATE_FORMAT}: {value}") from exc


def _parse_bool(value: str) -> bool:
    # Accept common CSV boolean spellings while storing true booleans internally.
    normalized = value.strip().lower()
    if normalized in {"true", "t", "yes", "y", "1"}:
        return True
    if normalized in {"false", "f", "no", "n", "0"}:
        return False
    raise ValueError(f"invalid boolean value: {value}")


def _calculate_age(birth_date: date, as_of: date) -> int:
    # Subtract one year when the patient has not reached their birthday yet.
    birthday_passed = (as_of.month, as_of.day) >= (birth_date.month, birth_date.day)
    return as_of.year - birth_date.year - (0 if birthday_passed else 1)


def _risk_tier(age: int, total_cost: Decimal, readmitted: bool) -> str:
    # Score combines age, encounter cost, and readmission as simple risk signals.
    score = 0
    if age >= 65:
        score += 2
    elif age >= 50:
        score += 1
    if total_cost >= Decimal("20000"):
        score += 2
    elif total_cost >= Decimal("5000"):
        score += 1
    if readmitted:
        score += 2

    if score >= 4:
        return "High"
    if score >= 2:
        return "Medium"
    return "Low"


def _risk_rank(risk_tier: str) -> int:
    # Numeric ranking makes it easy to compare tiers across a patient's encounters.
    return {"Low": 1, "Medium": 2, "High": 3}[risk_tier]
