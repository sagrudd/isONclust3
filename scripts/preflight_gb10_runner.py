"""GB10 runner contract checks for isONclust3 release preflight."""

from __future__ import annotations

from pathlib import Path


GB10_RUNNER = Path("scripts/run-gb10-benchmark.sh")
REQUIRED_RUNNER_MARKERS = (
    'export ISONCLUST3_FINAL_CLUSTERS="$run_out/clustering/final_clusters.tsv"',
    'final_checksum = sha256(final_clusters)',
    '"role": "final_clusters"',
    '"outputs": outputs',
    '"final_clusters_sha256"',
    '"contract_status"',
    '"thread_count"',
    '"peak_rss_mb"',
    '"container_digest"',
)
REQUIRED_TSV_FIELDS = (
    "project",
    "manifest_id",
    "benchmark_tier",
    "platform",
    "container_digest",
    "wall_time_seconds",
    "peak_rss_mb",
    "thread_count",
    "contract_status",
    "final_clusters_sha256",
)


def validate_gb10_runner(repo: Path) -> list[str]:
    path = repo / GB10_RUNNER
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"{GB10_RUNNER} is not readable: {exc}"]

    errors = [
        f"{GB10_RUNNER} missing report marker: {marker}"
        for marker in REQUIRED_RUNNER_MARKERS
        if marker not in text
    ]
    if '"accepted_contract" if exit_code == 0 and final_checksum' not in text:
        errors.append(
            f"{GB10_RUNNER} must require a final_clusters checksum for accepted_contract"
        )
    if "csv.DictWriter(" not in text or "delimiter=\"\\t\"" not in text:
        errors.append(f"{GB10_RUNNER} must write a tab-delimited TSV report")
    for field in REQUIRED_TSV_FIELDS:
        if f'"{field}"' not in text:
            errors.append(f"{GB10_RUNNER} TSV report missing field: {field}")
    if '"sha256": final_checksum' not in text:
        errors.append(f"{GB10_RUNNER} JSON outputs must expose final_clusters sha256")
    if '"final_clusters_sha256": final_checksum or ""' not in text:
        errors.append(f"{GB10_RUNNER} TSV row must expose final_clusters sha256")
    return errors
