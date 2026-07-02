"""Tracked artifact hygiene checks for isONclust3 release preflight."""

from __future__ import annotations

import subprocess
from pathlib import Path

FORBIDDEN_TRACKED_PREFIXES = (
    ".mypy_cache/",
    ".pytest_cache/",
    ".ruff_cache/",
    ".tox/",
    ".venv/",
    "target/",
    "venv/",
    "build/",
    "dist/",
    "docs/_build/",
    "htmlcov/",
    "scripts/__pycache__/",
    "__pycache__/",
    "benchmark-artifacts/",
    "benchmark-output/",
    "gb10-output/",
    "reports/",
    "gb10-reports/",
)
FORBIDDEN_TRACKED_SUFFIXES = (".pyc", ".pyo")
RAW_SEQUENCE_SUFFIXES = (
    ".bam",
    ".cram",
    ".sam",
    ".sra",
    ".pod5",
    ".fast5",
    ".fastq",
    ".fq",
    ".fasta",
    ".fa",
    ".fna",
    ".fastq.gz",
    ".fq.gz",
    ".fasta.gz",
    ".fa.gz",
    ".fna.gz",
)
ALLOWED_SEQUENCE_PREFIXES = ("fixtures/tiny/", "example_data/")


def validate_tracked_artifacts(repo: Path) -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=repo,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    errors = []
    for tracked in result.stdout.splitlines():
        if tracked.startswith(FORBIDDEN_TRACKED_PREFIXES) or tracked.endswith(
            FORBIDDEN_TRACKED_SUFFIXES
        ):
            errors.append(f"forbidden tracked artifact: {tracked}")
        if tracked.endswith(RAW_SEQUENCE_SUFFIXES) and not tracked.startswith(
            ALLOWED_SEQUENCE_PREFIXES
        ):
            errors.append(f"forbidden tracked raw sequencing artifact: {tracked}")
    return errors
