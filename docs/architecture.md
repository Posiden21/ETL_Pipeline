# Pipeline Architecture

## Overview

This project models a small healthcare batch ETL workflow.

```text
Raw CSV -> Extract -> Validate/Transform -> Curated CSV + SQLite Warehouse
```

## Extract

The extractor reads raw CSV files from `data/raw`. Each record is represented as a dictionary so validation can preserve original values for rejected-row auditing.

## Transform

The transform stage:

- Validates required identifiers and dates
- Rejects encounters where discharge date is before admit date
- Rejects negative encounter cost
- Standardizes booleans and categorical text
- Calculates patient age
- Calculates encounter length of stay
- Assigns patient risk tiers using age, readmission status, and cost
- Produces patient and encounter tables

## Load

The loader writes curated CSV files and replaces the SQLite warehouse tables:

- `patients`
- `encounters`
- `rejected_rows`

It also writes `data_quality_report.json`, which summarizes record counts, risk tiers, department volumes, and rejection reasons. This keeps local runs deterministic and easy to inspect.

## Portfolio Examples

The `examples` folder includes a walkthrough and SQL queries that can be used to demonstrate the finished warehouse:

- `examples/portfolio_walkthrough.md` shows the end-to-end demo flow.
- `examples/analytics_queries.sql` runs common analytical checks against SQLite.
- `healthcare-etl --show-examples` prints demo commands directly from the program after editable install.

## Possible Extensions

- Add FHIR JSON ingestion
- Add orchestration with Airflow or Dagster
- Add data quality reporting with Great Expectations
- Load into Postgres or a cloud warehouse
- Add incremental ingestion using watermarks
