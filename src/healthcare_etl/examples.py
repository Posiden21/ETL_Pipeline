"""Example commands and SQL snippets for portfolio demonstrations."""

from __future__ import annotations


# Keep the examples in code so the CLI and documentation can stay aligned.
EXAMPLE_USAGE = """\
Example pipeline run:
  healthcare-etl

Run with a custom source file:
  healthcare-etl \\
    --source data/raw/encounters.csv \\
    --output-dir data/processed \\
    --database data/processed/healthcare_warehouse.db

Inspect the SQLite warehouse:
  sqlite3 data/processed/healthcare_warehouse.db < examples/analytics_queries.sql

Useful portfolio talking points:
  - Raw encounters are validated before loading.
  - Rejected records are preserved with row numbers and reasons.
  - A JSON quality report summarizes validation and business-rule results.
  - Patient risk tiers are calculated from age, cost, and readmission status.
  - Curated CSVs and a relational SQLite warehouse are produced in one run.
"""


EXAMPLE_SQL = """\
-- Patient counts by risk tier.
SELECT
    risk_tier,
    COUNT(*) AS patient_count
FROM patients
GROUP BY risk_tier
ORDER BY patient_count DESC;

-- Average encounter cost and length of stay by department.
SELECT
    department,
    COUNT(*) AS encounter_count,
    ROUND(AVG(total_cost), 2) AS average_cost,
    ROUND(AVG(length_of_stay_days), 2) AS average_length_of_stay
FROM encounters
GROUP BY department
ORDER BY average_cost DESC;

-- Readmission rate by department.
SELECT
    department,
    COUNT(*) AS encounter_count,
    ROUND(100.0 * SUM(readmitted_30_days) / COUNT(*), 1) AS readmission_rate_pct
FROM encounters
GROUP BY department
ORDER BY readmission_rate_pct DESC;

-- Audit rejected rows after validation.
SELECT
    row_number,
    patient_id,
    encounter_id,
    reason
FROM rejected_rows
ORDER BY row_number;
"""
