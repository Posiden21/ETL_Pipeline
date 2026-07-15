"""Load curated healthcare data into files and SQLite."""

from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path

from .transform import TransformResult
from .visualization import write_department_cost_svg, write_risk_tier_svg


PATIENT_FIELDS = ["patient_id", "first_name", "last_name", "date_of_birth", "age", "gender", "risk_tier"]
ENCOUNTER_FIELDS = [
    "encounter_id",
    "patient_id",
    "admit_date",
    "discharge_date",
    "length_of_stay_days",
    "department",
    "diagnosis",
    "procedure_code",
    "total_cost",
    "readmitted_30_days",
]
REJECTED_FIELDS = ["row_number", "patient_id", "encounter_id", "reason"]


def load_outputs(result: TransformResult, output_dir: Path, database_path: Path) -> None:
    """Write transformed outputs to CSV and SQLite."""
    # The pipeline publishes both flat files for inspection and SQLite for querying.
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(output_dir / "patients.csv", result.patients, PATIENT_FIELDS)
    _write_csv(output_dir / "encounters.csv", result.encounters, ENCOUNTER_FIELDS)
    _write_csv(output_dir / "rejected_rows.csv", result.rejected_rows, REJECTED_FIELDS)
    _write_quality_report(output_dir / "data_quality_report.json", result)
    write_risk_tier_svg(output_dir / "risk_tiers.svg", result.patients)
    write_department_cost_svg(output_dir / "department_costs.svg", result.encounters)
    _load_sqlite(result, database_path)


def _write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    # Explicit field ordering keeps generated CSVs stable between runs.
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _write_quality_report(path: Path, result: TransformResult) -> None:
    # The report gives reviewers a quick audit view without opening every output file.
    report = {
        "valid_encounters": len(result.encounters),
        "rejected_rows": len(result.rejected_rows),
        "patients": len(result.patients),
        "risk_tier_counts": _count_by_field(result.patients, "risk_tier"),
        "department_counts": _count_by_field(result.encounters, "department"),
        "rejection_reasons": _count_rejection_reasons(result.rejected_rows),
    }
    with path.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2, sort_keys=True)
        file.write("\n")


def _count_by_field(rows: list[dict[str, object]], field: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = str(row[field])
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def _count_rejection_reasons(rows: list[dict[str, object]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        for reason in str(row["reason"]).split("; "):
            counts[reason] = counts.get(reason, 0) + 1
    return dict(sorted(counts.items()))


def _load_sqlite(result: TransformResult, database_path: Path) -> None:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(database_path) as connection:
        # Rebuild tables on each run so the warehouse mirrors the latest source file.
        connection.execute("DROP TABLE IF EXISTS patients")
        connection.execute("DROP TABLE IF EXISTS encounters")
        connection.execute("DROP TABLE IF EXISTS rejected_rows")
        connection.execute(
            """
            CREATE TABLE patients (
                patient_id TEXT PRIMARY KEY,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                date_of_birth TEXT NOT NULL,
                age INTEGER NOT NULL,
                gender TEXT NOT NULL,
                risk_tier TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE encounters (
                encounter_id TEXT PRIMARY KEY,
                patient_id TEXT NOT NULL,
                admit_date TEXT NOT NULL,
                discharge_date TEXT NOT NULL,
                length_of_stay_days INTEGER NOT NULL,
                department TEXT NOT NULL,
                diagnosis TEXT NOT NULL,
                procedure_code TEXT NOT NULL,
                total_cost REAL NOT NULL,
                readmitted_30_days INTEGER NOT NULL,
                FOREIGN KEY(patient_id) REFERENCES patients(patient_id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE rejected_rows (
                row_number INTEGER NOT NULL,
                patient_id TEXT,
                encounter_id TEXT,
                reason TEXT NOT NULL
            )
            """
        )

        # Use named parameters so insert statements follow the transformed record keys.
        connection.executemany(
            """
            INSERT INTO patients (
                patient_id, first_name, last_name, date_of_birth, age, gender, risk_tier
            ) VALUES (
                :patient_id, :first_name, :last_name, :date_of_birth, :age, :gender, :risk_tier
            )
            """,
            result.patients,
        )
        connection.executemany(
            """
            INSERT INTO encounters (
                encounter_id, patient_id, admit_date, discharge_date, length_of_stay_days,
                department, diagnosis, procedure_code, total_cost, readmitted_30_days
            ) VALUES (
                :encounter_id, :patient_id, :admit_date, :discharge_date, :length_of_stay_days,
                :department, :diagnosis, :procedure_code, :total_cost, :readmitted_30_days
            )
            """,
            result.encounters,
        )
        connection.executemany(
            """
            INSERT INTO rejected_rows (
                row_number, patient_id, encounter_id, reason
            ) VALUES (
                :row_number, :patient_id, :encounter_id, :reason
            )
            """,
            result.rejected_rows,
        )
