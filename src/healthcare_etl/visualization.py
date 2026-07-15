"""SVG chart writers for healthcare ETL portfolio outputs."""

from __future__ import annotations

from pathlib import Path


def write_risk_tier_svg(path: Path, patients: list[dict[str, object]]) -> None:
    counts = _count_by_field(patients, "risk_tier")
    ordered = [(tier, counts.get(tier, 0)) for tier in ["Low", "Medium", "High"]]
    colors = {"Low": "#22C55E", "Medium": "#F59E0B", "High": "#EF4444"}

    width, height = 860, 420
    margin_left, margin_top, plot_w, plot_h = 86, 72, 700, 260
    max_count = max(count for _, count in ordered) or 1
    bar_gap = 54
    bar_w = (plot_w - bar_gap * (len(ordered) - 1)) / len(ordered)

    lines = [
        _svg_header(width, height),
        f'<rect width="{width}" height="{height}" fill="#0F172A"/>',
        _text(30, 42, "Patient Risk Tier Distribution", size=24, weight=700),
        f'<rect x="{margin_left}" y="{margin_top}" width="{plot_w}" height="{plot_h}" fill="#172033" stroke="#334155"/>',
    ]

    for index, (tier, count) in enumerate(ordered):
        x = margin_left + index * (bar_w + bar_gap)
        bar_h = (count / max_count) * (plot_h - 34)
        y = margin_top + plot_h - bar_h
        lines.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{bar_h:.1f}" rx="6" fill="{colors[tier]}"/>')
        lines.append(_text(x + bar_w / 2 - 8, y - 12, str(count), size=18, weight=700))
        lines.append(_text(x + bar_w / 2 - 30, margin_top + plot_h + 30, tier, size=15, fill="#CBD5E1"))

    lines.append(_text(30, 390, "Risk tier is derived from age, total encounter cost, and readmission status.", size=13, fill="#94A3B8"))
    lines.append("</svg>")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_department_cost_svg(path: Path, encounters: list[dict[str, object]]) -> None:
    stats: dict[str, dict[str, float]] = {}
    for encounter in encounters:
        department = str(encounter["department"])
        stats.setdefault(department, {"count": 0, "cost": 0.0})
        stats[department]["count"] += 1
        stats[department]["cost"] += float(encounter["total_cost"])

    rows = sorted(
        [
            {
                "department": department,
                "count": int(values["count"]),
                "average_cost": values["cost"] / values["count"],
            }
            for department, values in stats.items()
        ],
        key=lambda row: float(row["average_cost"]),
        reverse=True,
    )

    width, height = 960, 520
    margin_left, margin_right, margin_top, margin_bottom = 178, 42, 72, 68
    plot_w = width - margin_left - margin_right
    row_h = 48
    max_cost = max(float(row["average_cost"]) for row in rows) or 1.0

    lines = [
        _svg_header(width, height),
        f'<rect width="{width}" height="{height}" fill="#0F172A"/>',
        _text(30, 42, "Average Encounter Cost by Department", size=24, weight=700),
        _text(30, 490, "Bar length shows average cost; label shows valid encounter count.", size=13, fill="#94A3B8"),
    ]

    for index, row in enumerate(rows):
        y = margin_top + index * row_h
        bar_w = (float(row["average_cost"]) / max_cost) * plot_w
        lines.append(_text(28, y + 26, str(row["department"]), size=14, fill="#CBD5E1"))
        lines.append(f'<rect x="{margin_left}" y="{y}" width="{plot_w}" height="30" rx="5" fill="#172033" stroke="#334155"/>')
        lines.append(f'<rect x="{margin_left}" y="{y}" width="{bar_w:.1f}" height="30" rx="5" fill="#38BDF8"/>')
        label = f"${float(row['average_cost']):,.0f} avg  |  {row['count']} encounters"
        lines.append(_text(margin_left + min(bar_w + 10, plot_w - 172), y + 21, label, size=12, fill="#F8FAFC", weight=700))

    lines.append("</svg>")
    path.write_text("\n".join(lines), encoding="utf-8")


def _count_by_field(rows: list[dict[str, object]], field: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = str(row[field])
        counts[value] = counts.get(value, 0) + 1
    return counts


def _svg_header(width: int, height: int) -> str:
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'


def _text(x: float, y: float, text: str, *, size: int, fill: str = "#F8FAFC", weight: int = 400) -> str:
    return f'<text x="{x:.1f}" y="{y:.1f}" fill="{fill}" font-family="Arial, Helvetica, sans-serif" font-size="{size}" font-weight="{weight}">{text}</text>'
