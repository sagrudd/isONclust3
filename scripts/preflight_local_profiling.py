"""Local profiling harness contract checks for isONclust3 release preflight."""

from __future__ import annotations

from pathlib import Path

LOCAL_PROFILING_SCRIPT = Path("scripts/run-local-profiling.sh")
REQUIRED_HELP_MARKERS = (
    "This is a developer profiling harness, not GB10 release evidence.",
    "--include-fastq-output",
    "--include-post-cluster",
    "--include-gff",
)
REQUIRED_JSON_MARKERS = (
    '"schema_version": 1',
    '"project": "isONclust3"',
    '"harness": "local-profiling"',
    '"release_evidence": False',
    '"wall_time_seconds": wall_time',
    '"peak_rss_mb": peak_rss_mb',
    '"final_clusters"',
    '"expected_sha256": expected_sha',
    '"contract_match": contract_match',
    '"optimization_facets"',
    '"seed-extraction"',
    '"cluster-assignment"',
    '"fastq-output" if "write-fastq" in variant else "handoff-no-fastq"',
    '"post-cluster" if "post-cluster" in variant else "default-clustering"',
    '"gff-assisted" if "gff" in variant else "de-novo-initialization"',
)
REQUIRED_TSV_FIELDS = (
    '"project"',
    '"case_id"',
    '"release_evidence"',
    '"wall_time_seconds"',
    '"peak_rss_mb"',
    '"exit_code"',
    '"contract_match"',
    '"final_clusters_sha256"',
)


def validate_local_profiling_harness(repo: Path) -> list[str]:
    path = repo / LOCAL_PROFILING_SCRIPT
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        return [f"{LOCAL_PROFILING_SCRIPT} is not readable: {error}"]

    errors: list[str] = []
    for marker in REQUIRED_HELP_MARKERS:
        if marker not in text:
            errors.append(f"{LOCAL_PROFILING_SCRIPT} missing help marker: {marker}")
    for marker in REQUIRED_JSON_MARKERS:
        if marker not in text:
            errors.append(f"{LOCAL_PROFILING_SCRIPT} missing JSON report marker: {marker}")
    for marker in REQUIRED_TSV_FIELDS:
        if marker not in text:
            errors.append(f"{LOCAL_PROFILING_SCRIPT} TSV report missing field: {marker}")
    if "raise SystemExit(1)" not in text or "if not contract_match:" not in text:
        errors.append(f"{LOCAL_PROFILING_SCRIPT} must fail when final_clusters contract mismatches")
    return errors
