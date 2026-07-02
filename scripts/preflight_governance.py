"""Governance document checks for isONclust3 release preflight."""

from __future__ import annotations

from pathlib import Path

REQUIRED_ACTIVE_BLOCKERS = {
    "ISOCLUST-BLOCK-001",
    "ISOCLUST-BLOCK-002",
    "ISOCLUST-BLOCK-003",
}
REQUIRED_RESOLVED_BLOCKERS = {
    "ISOCLUST-BLOCK-004",
}
REQUIRED_BENCHMARK_ACCEPTANCE_SECTIONS = (
    "## Required Report Fields",
    "## Acceptance Classes",
    "## Initial Gates",
)
REQUIRED_BENCHMARK_ACCEPTANCE_CLASSES = (
    "accepted_contract",
    "accepted_calibration",
    "rejected_contract",
    "rejected_operational",
    "blocked_pending_data",
)
REQUIRED_BENCHMARK_REPORT_MARKERS = (
    "Container image ID or digest.",
    "Host operating system, CPU architecture, platform target, and thread count.",
    "Input FASTQ checksum and generated `final_clusters.tsv` checksum.",
    "Full command line.",
    "Exit code, wall time, peak RSS status, and peak RSS when measurable.",
)


def validate_blockers(repo: Path) -> list[str]:
    path = repo / "BLOCKERS.md"
    text = path.read_text(encoding="utf-8")
    active_rows = {
        columns[0]
        for line in text.splitlines()
        if line.startswith("| ISOCLUST-BLOCK-")
        for columns in [[column.strip() for column in line.strip("|").split("|")]]
        if columns
    }

    errors: list[str] = []
    missing_active = REQUIRED_ACTIVE_BLOCKERS - active_rows
    if missing_active:
        errors.append(
            f"BLOCKERS.md missing active blocker row(s): "
            f"{', '.join(sorted(missing_active))}"
        )
    resolved_in_active = REQUIRED_RESOLVED_BLOCKERS & active_rows
    if resolved_in_active:
        errors.append(
            f"BLOCKERS.md resolved blocker(s) must not appear active: "
            f"{', '.join(sorted(resolved_in_active))}"
        )

    resolved_section = text.split("## Resolved Blockers", 1)
    if len(resolved_section) != 2:
        errors.append("BLOCKERS.md missing resolved blockers section")
        return errors
    for blocker in sorted(REQUIRED_RESOLVED_BLOCKERS):
        if blocker not in resolved_section[1]:
            errors.append(f"BLOCKERS.md missing resolved blocker marker: {blocker}")
    return errors


def validate_benchmark_acceptance(repo: Path) -> list[str]:
    path = repo / "BENCHMARK_ACCEPTANCE.md"
    text = path.read_text(encoding="utf-8")
    errors = [
        f"BENCHMARK_ACCEPTANCE.md missing section: {section}"
        for section in REQUIRED_BENCHMARK_ACCEPTANCE_SECTIONS
        if section not in text
    ]
    for class_name in REQUIRED_BENCHMARK_ACCEPTANCE_CLASSES:
        if f"- `{class_name}`:" not in text:
            errors.append(
                f"BENCHMARK_ACCEPTANCE.md missing acceptance class: {class_name}"
            )
    for marker in REQUIRED_BENCHMARK_REPORT_MARKERS:
        if marker not in text:
            errors.append(
                f"BENCHMARK_ACCEPTANCE.md missing required report marker: {marker}"
            )
    return errors
