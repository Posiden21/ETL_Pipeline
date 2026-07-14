"""Extract raw encounter records from CSV files."""

from __future__ import annotations

import csv
from pathlib import Path


def extract_encounters(source_path: Path) -> list[dict[str, str]]:
    """Read encounter rows from a CSV file."""
    # DictReader keeps each CSV row keyed by header name for downstream validation.
    with source_path.open("r", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))
