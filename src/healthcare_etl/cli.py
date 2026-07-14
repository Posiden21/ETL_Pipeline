"""Command-line interface for the healthcare ETL pipeline."""

from __future__ import annotations

import argparse
from pathlib import Path

from .examples import EXAMPLE_SQL, EXAMPLE_USAGE
from .pipeline import run_pipeline


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE = PROJECT_ROOT / "data" / "raw" / "encounters.csv"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"
DEFAULT_DATABASE = DEFAULT_OUTPUT_DIR / "healthcare_warehouse.db"


def build_parser() -> argparse.ArgumentParser:
    # Defaults point at the repository data folders so local runs need no arguments.
    parser = argparse.ArgumentParser(
        description="Run the Healthcare ETL Pipeline.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Use --show-examples to print demo commands and analytics queries.",
    )
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE, help="Path to the raw encounters CSV.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Directory for curated CSV outputs.")
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE, help="SQLite warehouse path.")
    parser.add_argument("--show-examples", action="store_true", help="Print demo commands for portfolio walkthroughs.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.show_examples:
        print(EXAMPLE_USAGE)
        print("Example analytics SQL:")
        print(EXAMPLE_SQL)
        return

    # Delegate work to the pipeline layer and keep CLI output focused on the run summary.
    summary = run_pipeline(
        source_path=args.source,
        output_dir=args.output_dir,
        database_path=args.database,
    )
    print("Pipeline complete")
    print(f"Valid encounters: {summary.valid_encounters}")
    print(f"Rejected rows: {summary.rejected_rows}")
    print(f"Output directory: {summary.output_dir}")
    print(f"SQLite warehouse: {summary.database_path}")


if __name__ == "__main__":
    main()
