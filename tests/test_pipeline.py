from __future__ import annotations

import csv
import sqlite3
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from healthcare_etl.pipeline import run_pipeline
from healthcare_etl.transform import transform_encounters


class TransformTests(unittest.TestCase):
    def test_transform_rejects_invalid_rows_and_assigns_risk(self) -> None:
        rows = [
            {
                "patient_id": "P001",
                "first_name": "avery",
                "last_name": "johnson",
                "date_of_birth": "1950-01-01",
                "gender": "f",
                "encounter_id": "E1",
                "admit_date": "2026-01-01",
                "discharge_date": "2026-01-03",
                "department": "cardiology",
                "diagnosis": "Hypertension",
                "procedure_code": "i10",
                "total_cost": "25000",
                "readmitted_30_days": "true",
            },
            {
                "patient_id": "P002",
                "first_name": "bad",
                "last_name": "date",
                "date_of_birth": "1990-01-01",
                "gender": "m",
                "encounter_id": "E2",
                "admit_date": "2026-01-05",
                "discharge_date": "2026-01-04",
                "department": "emergency",
                "diagnosis": "Chest pain",
                "procedure_code": "R07",
                "total_cost": "1200",
                "readmitted_30_days": "false",
            },
        ]

        result = transform_encounters(rows, as_of=date(2026, 7, 7))

        self.assertEqual(len(result.encounters), 1)
        self.assertEqual(len(result.rejected_rows), 1)
        self.assertEqual(result.patients[0]["first_name"], "Avery")
        self.assertEqual(result.patients[0]["risk_tier"], "High")
        self.assertEqual(result.encounters[0]["length_of_stay_days"], 2)
        self.assertIn("discharge_date", result.rejected_rows[0]["reason"])


class PipelineTests(unittest.TestCase):
    def test_pipeline_writes_csv_and_sqlite_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir_name:
            temp_dir = Path(temp_dir_name)
            source = temp_dir / "encounters.csv"
            output_dir = temp_dir / "processed"
            database = output_dir / "warehouse.db"

            with source.open("w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(
                    [
                        "patient_id",
                        "first_name",
                        "last_name",
                        "date_of_birth",
                        "gender",
                        "encounter_id",
                        "admit_date",
                        "discharge_date",
                        "department",
                        "diagnosis",
                        "procedure_code",
                        "total_cost",
                        "readmitted_30_days",
                    ]
                )
                writer.writerow(
                    [
                        "P001",
                        "Avery",
                        "Johnson",
                        "1984-02-19",
                        "F",
                        "E1001",
                        "2026-01-03",
                        "2026-01-06",
                        "Cardiology",
                        "Hypertension",
                        "I10",
                        "4200.50",
                        "false",
                    ]
                )

            summary = run_pipeline(source_path=source, output_dir=output_dir, database_path=database)

            self.assertEqual(summary.valid_encounters, 1)
            self.assertEqual(summary.rejected_rows, 0)
            self.assertEqual(summary.output_dir, output_dir)
            self.assertTrue((output_dir / "patients.csv").exists())
            self.assertTrue((output_dir / "data_quality_report.json").exists())
            self.assertTrue((output_dir / "risk_tiers.svg").exists())
            self.assertTrue((output_dir / "department_costs.svg").exists())
            self.assertTrue(database.exists())

            with sqlite3.connect(database) as connection:
                patient_count = connection.execute("SELECT COUNT(*) FROM patients").fetchone()[0]
                encounter_count = connection.execute("SELECT COUNT(*) FROM encounters").fetchone()[0]

            self.assertEqual(patient_count, 1)
            self.assertEqual(encounter_count, 1)


if __name__ == "__main__":
    unittest.main()
