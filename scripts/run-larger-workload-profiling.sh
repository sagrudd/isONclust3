#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Run local isONclust3 profiling against an externally staged accepted workload.

This is profiling evidence for optimization planning, not GB10 release evidence.
Raw reports are written under target/ by default and must not be committed.

Required:
  --manifest FILE                 Benchmark manifest JSON.
  --fastq FILE                    Externally staged FASTQ input.

Optional:
  --expected-final-clusters FILE  Expected final_clusters.tsv for exact
                                  compatibility comparison.
  --output-dir DIR                Report/output root. Default: target/larger-profile.
  --binary PATH                   Existing isONclust3 binary. Default: target/release/isONclust3.
  --skip-build                    Reuse --binary without cargo build --release.
  --variant NAME                  default-no-fastq, write-fastq, post-cluster,
                                  or post-cluster-write-fastq.
  --case-id ID                    Stable report case ID. Default: manifest ID plus variant.
  -h, --help                      Show this help.
USAGE
}

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
manifest_path=""
fastq_path=""
expected_final_clusters=""
output_dir="$repo_root/target/larger-profile"
binary="$repo_root/target/release/isONclust3"
skip_build="false"
variant="default-no-fastq"
case_id=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --manifest)
      manifest_path="$2"
      shift 2
      ;;
    --fastq)
      fastq_path="$2"
      shift 2
      ;;
    --expected-final-clusters)
      expected_final_clusters="$2"
      shift 2
      ;;
    --output-dir)
      output_dir="$2"
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
    --variant)
      variant="$2"
      shift 2
      ;;
    --case-id)
      case_id="$2"
      shift 2
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

if [[ -z "$manifest_path" || -z "$fastq_path" ]]; then
  echo "--manifest and --fastq are required" >&2
  usage >&2
  exit 2
fi
case "$variant" in
  default-no-fastq|write-fastq|post-cluster|post-cluster-write-fastq) ;;
  *)
    echo "--variant must be default-no-fastq, write-fastq, post-cluster, or post-cluster-write-fastq" >&2
    exit 2
    ;;
esac

manifest_path="$(cd "$(dirname "$manifest_path")" && pwd)/$(basename "$manifest_path")"
fastq_path="$(cd "$(dirname "$fastq_path")" && pwd)/$(basename "$fastq_path")"
if [[ -n "$expected_final_clusters" ]]; then
  expected_final_clusters="$(cd "$(dirname "$expected_final_clusters")" && pwd)/$(basename "$expected_final_clusters")"
fi
if [[ ! -f "$manifest_path" ]]; then
  echo "missing manifest: $manifest_path" >&2
  exit 2
fi
if [[ ! -f "$fastq_path" ]]; then
  echo "missing FASTQ: $fastq_path" >&2
  exit 2
fi
if [[ -n "$expected_final_clusters" && ! -f "$expected_final_clusters" ]]; then
  echo "missing expected final_clusters.tsv: $expected_final_clusters" >&2
  exit 2
fi

eval "$(
  python3 - "$manifest_path" <<'PY'
import json
import shlex
import sys

manifest = json.load(open(sys.argv[1], encoding="utf-8"))
acceptance = manifest.get("acceptance", {})
values = {
    "manifest_id": manifest.get("manifest_id", ""),
    "benchmark_tier": manifest.get("benchmark_tier", ""),
    "mode": manifest.get("mode", ""),
    "seeding": manifest.get("seeding", ""),
    "expected_sha": acceptance.get("final_clusters_sha256", ""),
}
for key, value in values.items():
    print(f"manifest_{key}={shlex.quote(str(value))}")
PY
)"

if [[ -z "$manifest_manifest_id" || -z "$manifest_mode" || -z "$manifest_seeding" ]]; then
  echo "manifest is missing manifest_id, mode, or seeding" >&2
  exit 2
fi
if [[ -z "$case_id" ]]; then
  case_id="$manifest_manifest_id-$variant"
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
run_dir="$output_dir/$case_id/isonclust3"
reports_dir="$output_dir/reports"
report_json="$reports_dir/$case_id.json"
report_tsv="$reports_dir/$case_id.tsv"
log_file="$reports_dir/$case_id.log"
rm -rf "$output_dir/$case_id"
mkdir -p "$run_dir" "$reports_dir"

cmd=(
  "$binary"
  --fastq "$fastq_path"
  --mode "$manifest_mode"
  --outfolder "$run_dir"
  --seeding "$manifest_seeding"
)
if [[ "$variant" == "default-no-fastq" || "$variant" == "post-cluster" ]]; then
  cmd+=(--no-fastq)
fi
if [[ "$variant" == "post-cluster" || "$variant" == "post-cluster-write-fastq" ]]; then
  cmd+=(--post-cluster)
fi

python3 - \
  "$manifest_path" \
  "$fastq_path" \
  "$expected_final_clusters" \
  "$report_json" \
  "$report_tsv" \
  "$log_file" \
  "$run_dir" \
  "$case_id" \
  "$variant" \
  "$manifest_manifest_id" \
  "$manifest_benchmark_tier" \
  "$manifest_mode" \
  "$manifest_seeding" \
  "$manifest_expected_sha" \
  "${cmd[@]}" <<'PY'
import csv
import hashlib
import json
import platform
import resource
import subprocess
import sys
import time
from pathlib import Path

manifest_path = Path(sys.argv[1])
fastq = Path(sys.argv[2])
expected_path = Path(sys.argv[3]) if sys.argv[3] else None
report_json = Path(sys.argv[4])
report_tsv = Path(sys.argv[5])
log_file = Path(sys.argv[6])
run_dir = Path(sys.argv[7])
case_id = sys.argv[8]
variant = sys.argv[9]
manifest_id = sys.argv[10]
benchmark_tier = sys.argv[11]
mode = sys.argv[12]
seeding = sys.argv[13]
manifest_expected_sha = sys.argv[14] or None
cmd = sys.argv[15:]


def sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
profiling_plan = manifest.get("profiling_plan", {})
start = time.perf_counter()
with log_file.open("w", encoding="utf-8") as log:
    result = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, check=False)
wall_time = round(time.perf_counter() - start, 6)

ru_maxrss = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
if sys.platform == "darwin":
    peak_rss_mb = round(ru_maxrss / 1024 / 1024, 3)
else:
    peak_rss_mb = round(ru_maxrss / 1024, 3)

final_clusters = run_dir / "clustering" / "final_clusters.tsv"
observed_sha = sha256(final_clusters)
expected_sha = sha256(expected_path) if expected_path else manifest_expected_sha
contract_match = (
    result.returncode == 0
    and observed_sha is not None
    and expected_sha is not None
    and observed_sha == expected_sha
)

report = {
    "schema_version": 1,
    "project": "isONclust3",
    "harness": "larger-workload-profiling",
    "release_evidence": False,
    "case_id": case_id,
    "manifest_id": manifest_id,
    "benchmark_tier": benchmark_tier,
    "mode": mode,
    "seeding": seeding,
    "variant": variant,
    "source_manifest": str(manifest_path),
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
    "profiling_plan": profiling_plan,
    "optimization_facets": [
        "seed-generation",
        "minimizer-extraction" if seeding == "minimizer" else "syncmer-extraction",
        "quality-filtering",
        "final-clusters-contract",
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
            "manifest_id",
            "benchmark_tier",
            "variant",
            "exit_code",
            "wall_time_seconds",
            "peak_rss_mb",
            "final_clusters_sha256",
            "expected_sha256",
            "contract_match",
            "report_json",
            "log",
        ],
        delimiter="\t",
    )
    writer.writeheader()
    writer.writerow(
        {
            "project": "isONclust3",
            "case_id": case_id,
            "release_evidence": "false",
            "manifest_id": manifest_id,
            "benchmark_tier": benchmark_tier,
            "variant": variant,
            "exit_code": result.returncode,
            "wall_time_seconds": wall_time,
            "peak_rss_mb": peak_rss_mb,
            "final_clusters_sha256": observed_sha or "",
            "expected_sha256": expected_sha or "",
            "contract_match": str(contract_match).lower(),
            "report_json": str(report_json),
            "log": str(log_file),
        }
    )

if result.returncode != 0:
    raise SystemExit(result.returncode)
if expected_sha and not contract_match:
    raise SystemExit("final_clusters contract mismatch")
PY

echo "wrote $report_json"
echo "wrote $report_tsv"
