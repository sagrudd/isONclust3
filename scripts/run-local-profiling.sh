#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Run local isONclust3 toy profiling and write JSON/TSV reports.

This is a developer profiling harness, not GB10 release evidence.

Options:
  --output-dir DIR         Report/output root. Default: target/local-profile.
  --case CASE              ont, pacbio, or all. Default: all.
  --binary PATH            Existing isONclust3 binary. Default: target/release/isONclust3.
  --skip-build             Reuse --binary without running cargo build --release.
  --include-fastq-output   Also profile per-cluster FASTQ output.
  --include-post-cluster   Also profile post-clustering refinement.
  -h, --help               Show this help.
USAGE
}

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
output_dir="$repo_root/target/local-profile"
case_filter="all"
binary="$repo_root/target/release/isONclust3"
skip_build="false"
include_fastq_output="false"
include_post_cluster="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --output-dir)
      output_dir="$2"
      shift 2
      ;;
    --case)
      case_filter="$2"
      shift 2
      ;;
    --binary)
      binary="$2"
      shift 2
      ;;
    --skip-build)
      skip_build="true"
      shift
      ;;
    --include-fastq-output)
      include_fastq_output="true"
      shift
      ;;
    --include-post-cluster)
      include_post_cluster="true"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ "$case_filter" != "all" && "$case_filter" != "ont" && "$case_filter" != "pacbio" ]]; then
  echo "--case must be ont, pacbio, or all" >&2
  exit 2
fi

if [[ "$skip_build" != "true" ]]; then
  cargo build --release --manifest-path "$repo_root/Cargo.toml"
fi
if [[ ! -x "$binary" ]]; then
  echo "missing executable binary: $binary" >&2
  exit 2
fi

mkdir -p "$output_dir"
output_dir="$(cd "$output_dir" && pwd)"

run_case() {
  local mode="$1"
  local variant="$2"
  local input_dir="$repo_root/fixtures/tiny/$mode"
  local fastq="$input_dir/reads.fastq"
  local expected="$input_dir/expected/final_clusters.tsv"
  local run_dir="$output_dir/$mode-$variant/isonclust3"
  local report_json="$output_dir/$mode-$variant.json"
  local report_tsv="$output_dir/$mode-$variant.tsv"
  local log_file="$output_dir/$mode-$variant.log"
  local -a extra_args=()

  rm -rf "$output_dir/$mode-$variant"
  mkdir -p "$run_dir"

  if [[ "$variant" == *"no-fastq"* ]]; then
    extra_args+=(--no-fastq)
  fi
  if [[ "$variant" == *"post-cluster"* ]]; then
    extra_args+=(--post-cluster)
  fi

  python3 - \
    "$binary" \
    "$fastq" \
    "$mode" \
    "$run_dir" \
    "$expected" \
    "$report_json" \
    "$report_tsv" \
    "$log_file" \
    "$variant" \
    "${extra_args[@]}" <<'PY'
import csv
import hashlib
import json
import os
import platform
import resource
import subprocess
import sys
import time
from pathlib import Path

binary = Path(sys.argv[1])
fastq = Path(sys.argv[2])
mode = sys.argv[3]
out_dir = Path(sys.argv[4])
expected = Path(sys.argv[5])
report_json = Path(sys.argv[6])
report_tsv = Path(sys.argv[7])
log_file = Path(sys.argv[8])
variant = sys.argv[9]
extra_args = sys.argv[10:]


def sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


cmd = [
    str(binary),
    "--fastq",
    str(fastq),
    "--mode",
    mode,
    "--outfolder",
    str(out_dir),
    "--seeding",
    "minimizer",
    *extra_args,
]

start = time.perf_counter()
with log_file.open("w", encoding="utf-8") as log:
    result = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, check=False)
wall_time = round(time.perf_counter() - start, 6)

ru_maxrss = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
if sys.platform == "darwin":
    peak_rss_mb = round(ru_maxrss / 1024 / 1024, 3)
else:
    peak_rss_mb = round(ru_maxrss / 1024, 3)

final_clusters = out_dir / "clustering" / "final_clusters.tsv"
expected_sha = sha256(expected)
observed_sha = sha256(final_clusters)
contract_match = (
    result.returncode == 0
    and expected_sha is not None
    and observed_sha is not None
    and expected_sha == observed_sha
)

report = {
    "schema_version": 1,
    "project": "isONclust3",
    "harness": "local-profiling",
    "release_evidence": False,
    "case_id": f"{mode}-{variant}",
    "mode": mode,
    "seeding": "minimizer",
    "variant": variant,
    "command": cmd,
    "exit_code": result.returncode,
    "host_os": platform.system(),
    "host_architecture": platform.machine(),
    "metrics": {
        "wall_time_seconds": wall_time,
        "peak_rss_mb": peak_rss_mb,
    },
    "inputs": [
        {
            "role": "input_fastq",
            "path": str(fastq),
            "sha256": sha256(fastq),
        }
    ],
    "outputs": [
        {
            "role": "final_clusters",
            "path": str(final_clusters),
            "sha256": observed_sha,
            "expected_sha256": expected_sha,
            "contract_match": contract_match,
        }
    ],
    "optimization_facets": [
        "seed-extraction",
        "cluster-assignment",
        "fastq-output" if "write-fastq" in variant else "handoff-no-fastq",
        "post-cluster" if "post-cluster" in variant else "default-clustering",
    ],
    "log": str(log_file),
}
report_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

with report_tsv.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(
        handle,
        fieldnames=[
            "project",
            "case_id",
            "release_evidence",
            "wall_time_seconds",
            "peak_rss_mb",
            "exit_code",
            "contract_match",
            "final_clusters_sha256",
        ],
        delimiter="\t",
    )
    writer.writeheader()
    writer.writerow(
        {
            "project": report["project"],
            "case_id": report["case_id"],
            "release_evidence": report["release_evidence"],
            "wall_time_seconds": wall_time,
            "peak_rss_mb": peak_rss_mb,
            "exit_code": result.returncode,
            "contract_match": contract_match,
            "final_clusters_sha256": observed_sha or "",
        }
    )

if not contract_match:
    raise SystemExit(1)
PY

  echo "wrote $report_json"
  echo "wrote $report_tsv"
}

for mode in ont pacbio; do
  if [[ "$case_filter" != "all" && "$case_filter" != "$mode" ]]; then
    continue
  fi
  run_case "$mode" "no-fastq"
  if [[ "$include_fastq_output" == "true" ]]; then
    run_case "$mode" "write-fastq"
  fi
  if [[ "$include_post_cluster" == "true" ]]; then
    run_case "$mode" "no-fastq-post-cluster"
  fi
done

echo "local profiling passed: $output_dir"

