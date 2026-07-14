# Healthcare ETL Pipeline

A Python ETL project that ingests raw healthcare encounter data, validates and standardizes it, and loads curated analytics tables into SQLite.

The project is intentionally lightweight: it uses the Python standard library only, so reviewers can clone it and run the pipeline without dependency setup.

## What It Demonstrates

- Batch ETL design with clear extract, transform, and load stages
- Data quality checks for required fields, dates, duplicates, and numeric values
- Healthcare-oriented transformations such as risk tiering, length-of-stay, and encounter summaries
- SQLite warehouse loading with dimensional and fact-style tables
- Automated tests for transformation and pipeline behavior
- Clean project structure suitable for a GitHub profile

## Project Structure

```text
.
├── data/
│   ├── raw/                  # Source CSV files
│   └── processed/            # Generated curated CSV outputs
├── docs/
│   └── architecture.md       # Pipeline design notes
├── examples/
│   ├── analytics_queries.sql # Ready-to-run warehouse queries
│   └── portfolio_walkthrough.md
├── src/
│   └── healthcare_etl/
│       ├── cli.py            # Command-line entry point
│       ├── examples.py       # Demo commands and SQL snippets
│       ├── extract.py        # CSV extraction
│       ├── load.py           # SQLite and CSV loading
│       ├── pipeline.py       # End-to-end orchestration
│       └── transform.py      # Validation and business rules
├── tests/
│   └── test_pipeline.py
└── requirements.txt
```

## Quick Start

Run the pipeline with the included sample data:

```bash
python3 -m src.healthcare_etl.cli
```

Expected output:

```text
Pipeline complete
Valid encounters: 8
Rejected rows: 2
SQLite warehouse: /path/to/healthcare-etl-pipeline/data/processed/healthcare_warehouse.db
```

The run creates:

- `data/processed/patients.csv`
- `data/processed/encounters.csv`
- `data/processed/rejected_rows.csv`
- `data/processed/healthcare_warehouse.db`

Print a portfolio-friendly walkthrough from the CLI:

```bash
python3 -m src.healthcare_etl.cli --show-examples
```

## Run Tests

```bash
python3 -m unittest discover -s tests
```

## Example Analytics Queries

After running the pipeline:

```bash
sqlite3 data/processed/healthcare_warehouse.db < examples/analytics_queries.sql
```

You can also open the database interactively:

```bash
sqlite3 data/processed/healthcare_warehouse.db
```

```sql
SELECT risk_tier, COUNT(*) AS patients
FROM patients
GROUP BY risk_tier;

SELECT department, ROUND(AVG(total_cost), 2) AS avg_cost
FROM encounters
GROUP BY department
ORDER BY avg_cost DESC;
```

For a guided demo script, see `examples/portfolio_walkthrough.md`.

## Data Model

### `patients`

One row per patient with demographics and risk tier.

### `encounters`

One row per valid encounter with visit dates, diagnosis, department, cost, and calculated length of stay.

### `rejected_rows`

Rows that failed validation, with rejection reasons for auditability.

## Notes

The sample dataset is synthetic and does not contain protected health information. It is designed for demonstration only.
