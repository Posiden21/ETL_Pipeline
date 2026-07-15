# Portfolio Walkthrough

Use this script when showing the project to recruiters, hiring managers, or other engineers.

## 1. Run the ETL job

```bash
python3 -m pip install -e .
healthcare-etl
```

Expected output:

```text
Pipeline complete
Valid encounters: 8
Rejected rows: 2
Output directory: /path/to/healthcare-etl-pipeline/data/processed
SQLite warehouse: /path/to/healthcare-etl-pipeline/data/processed/healthcare_warehouse.db
```

## 2. Inspect generated files

```bash
ls data/processed
```

The job creates curated CSVs for easy inspection and a SQLite warehouse for analytics:

- `patients.csv`
- `encounters.csv`
- `rejected_rows.csv`
- `data_quality_report.json`
- `risk_tiers.svg`
- `department_costs.svg`
- `healthcare_warehouse.db`

## 3. Run analytics queries

```bash
sqlite3 data/processed/healthcare_warehouse.db < examples/analytics_queries.sql
```

These queries show patient risk tiers, department-level encounter metrics, readmission rates, and rejected-row audit output.

## 4. Talking points

- The extractor reads raw CSV data into dictionaries keyed by source headers.
- The transform layer validates required fields, dates, duplicate encounters, costs, and boolean values.
- Valid records are standardized into patient and encounter tables.
- Invalid records are preserved in `rejected_rows` with row numbers and reasons, which mirrors real data quality workflows.
- The JSON quality report gives a concise audit summary for reviewers.
- The SVG charts give a quick visual summary without any plotting dependency.
- The loader publishes both flat files and SQLite tables, making the result useful for data review and analytics.
