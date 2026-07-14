"""End-to-end pipeline orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

from .extract import extract_encounters
from .load import load_outputs
from .transform import transform_encounters


@dataclass(frozen=True)
class PipelineSummary:
    # Minimal run metadata is returned to the CLI and tests after a successful load.
    valid_encounters: int
    rejected_rows: int
    database_path: Path
    output_dir: Path


def run_pipeline(
    source_path: Path,
    output_dir: Path,
    database_path: Path,
    as_of: date | None = None,
) -> PipelineSummary:
    """Run the healthcare ETL pipeline."""
    # Keep orchestration thin: each stage owns its own extract, transform, or load details.
    raw_rows = extract_encounters(source_path)
    result = transform_encounters(raw_rows, as_of=as_of)
    load_outputs(result, output_dir=output_dir, database_path=database_path)

    return PipelineSummary(
        valid_encounters=len(result.encounters),
        rejected_rows=len(result.rejected_rows),
        database_path=database_path,
        output_dir=output_dir,
    )
