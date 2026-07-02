"""CI workflow checks for isONclust3 release preflight."""

from __future__ import annotations

from pathlib import Path

REQUIRED_CI_MARKERS = (
    "actions/setup-python@v5",
    "python -m pip install -r docs/requirements.txt",
    "cargo fmt --check",
    "cargo test",
    "cargo clippy --all-targets -- -D warnings",
    "scripts/check-output-contract-fixtures.sh",
    "scripts/run-local-profiling.sh --case all --include-fastq-output --include-post-cluster --include-gff",
    "sphinx-build -W -b html docs target/sphinx-html",
    "scripts/release-preflight.py",
)


def validate_ci(repo: Path) -> list[str]:
    workflow = repo / ".github" / "workflows" / "ci.yml"
    if not workflow.is_file():
        return ["missing .github/workflows/ci.yml"]
    text = workflow.read_text(encoding="utf-8")
    return [
        f"CI workflow missing marker: {marker}"
        for marker in REQUIRED_CI_MARKERS
        if marker not in text
    ]
