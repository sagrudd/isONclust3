#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Run a containerized isONclust3 benchmark and write checksum-backed reports.

Required:
  --input-dir DIR       Host directory containing the FASTQ input.
  --output-dir DIR      Host directory for isONclust3 outputs and reports.

Optional:
  --manifest FILE       Benchmark manifest JSON used for report metadata.
  --image IMAGE         Container image to run. Default: isonclust3:gb10.
  --platform PLATFORM   Docker platform. Default: linux/arm64.
  --fastq NAME          FASTQ filename inside input-dir. Default: reads.fastq.
  --mode MODE           isONclust3 mode: ont or pacbio. Default: ont.
  --seeding MODE        Seeding mode. Default: minimizer.
  --run-id ID           Immutable run ID. Default: UTC timestamp.
  --threads N           Thread count recorded in report metadata. Default: 1.
  --container-name NAME Docker container name. Default: derived from run ID.
  --write-fastq         Allow per-cluster FASTQ output by omitting --no-fastq.
  -h, --help            Show this help.
USAGE
}

safe_token() {
  printf '%s' "$1" \
    | tr '[:upper:]' '[:lower:]' \
    | sed -E 's#[ /]+#-#g; s#[^a-z0-9._:-]#-#g; s#-+#-#g; s#^-##; s#-$##'
}

image="isonclust3:gb10"
platform="linux/arm64"
fastq_name="reads.fastq"
mode="ont"
seeding="minimizer"
run_id="$(date -u +"%Y%m%dT%H%M%SZ")"
threads="1"
container_name=""
input_dir=""
output_dir=""
manifest_path=""
manifest_id="manual-isonclust3-run"
benchmark_tier="manual"
write_fastq="false"
image_set="false"
mode_set="false"
seeding_set="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --manifest) manifest_path="$2"; shift 2 ;;
    --input-dir) input_dir="$2"; shift 2 ;;
    --output-dir) output_dir="$2"; shift 2 ;;
    --image) image="$2"; image_set="true"; shift 2 ;;
    --platform) platform="$2"; shift 2 ;;
    --fastq) fastq_name="$2"; shift 2 ;;
    --mode) mode="$2"; mode_set="true"; shift 2 ;;
    --seeding) seeding="$2"; seeding_set="true"; shift 2 ;;
    --run-id) run_id="$2"; shift 2 ;;
    --threads) threads="$2"; shift 2 ;;
    --container-name) container_name="$2"; shift 2 ;;
    --write-fastq) write_fastq="true"; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

if [[ -n "$manifest_path" ]]; then
  manifest_path="$(cd "$(dirname "$manifest_path")" && pwd)/$(basename "$manifest_path")"
  if [[ ! -f "$manifest_path" ]]; then
    echo "missing benchmark manifest: $manifest_path" >&2
    exit 2
  fi
  eval "$(
    python3 - "$manifest_path" <<'PY'
import json
import shlex
import sys

manifest = json.load(open(sys.argv[1], encoding="utf-8"))
values = {
    "manifest_id": manifest.get("manifest_id", ""),
    "benchmark_tier": manifest.get("benchmark_tier", ""),
    "mode": manifest.get("mode", ""),
    "seeding": manifest.get("seeding", ""),
    "image": manifest.get("command", {}).get("container_image", ""),
}
for key, value in values.items():
    print(f"manifest_{key}={shlex.quote(str(value))}")
PY
  )"
  [[ -n "$manifest_manifest_id" ]] && manifest_id="$manifest_manifest_id"
  [[ -n "$manifest_benchmark_tier" ]] && benchmark_tier="$manifest_benchmark_tier"
  [[ "$mode_set" == "false" && -n "$manifest_mode" ]] && mode="$manifest_mode"
  [[ "$seeding_set" == "false" && -n "$manifest_seeding" ]] && seeding="$manifest_seeding"
  [[ "$image_set" == "false" && -n "$manifest_image" ]] && image="$manifest_image"
fi

if [[ -z "$input_dir" || -z "$output_dir" ]]; then
  echo "--input-dir and --output-dir are required" >&2
  usage >&2
  exit 2
fi
if [[ "$mode" != "ont" && "$mode" != "pacbio" ]]; then
  echo "--mode must be ont or pacbio" >&2
  exit 2
fi

input_dir="$(cd "$input_dir" && pwd)"
mkdir -p "$output_dir"
output_dir="$(cd "$output_dir" && pwd)"
fastq_host="$input_dir/$fastq_name"
if [[ ! -f "$fastq_host" ]]; then
  echo "missing FASTQ: $fastq_host" >&2
  exit 2
fi

if [[ -z "$container_name" ]]; then
  container_name="isonclust3-$(safe_token "$run_id" | tr ':' '-')"
fi

report_base="isonclust3__$(safe_token "$manifest_id")__$(safe_token "$benchmark_tier")__$(safe_token "$platform")__$(safe_token "$run_id")"
reports_dir="$output_dir/reports"
run_out="$output_dir/isonclust3"
mkdir -p "$reports_dir" "$run_out"
report_json="$reports_dir/${report_base}.json"
report_tsv="$reports_dir/${report_base}.tsv"
run_log="$reports_dir/${report_base}.log"
stats_log="$reports_dir/${report_base}.docker-stats.tsv"

cmd=(
  docker run --rm
  --name "$container_name"
  --platform "$platform"
  --volume "$input_dir:/work/data:ro"
  --volume "$output_dir:/work/out"
  "$image"
  --fastq "/work/data/$fastq_name"
  --mode "$mode"
  --outfolder "/work/out/isonclust3"
  --seeding "$seeding"
)
if [[ "$write_fastq" != "true" ]]; then
  cmd+=(--no-fastq)
fi

container_digest="$(docker image inspect --format '{{index .RepoDigests 0}}' "$image" 2>/dev/null || true)"
if [[ -z "$container_digest" ]]; then
  container_digest="$(docker image inspect --format '{{.Id}}' "$image" 2>/dev/null || echo "image-not-inspected")"
fi

peak_rss_bytes=0
peak_rss_mb=""
peak_rss_status="not_collected"
: >"$stats_log"

start_time="$(python3 -c 'import time; print(time.time())')"
set +e
"${cmd[@]}" >"$run_log" 2>&1 &
docker_pid=$!
while kill -0 "$docker_pid" 2>/dev/null; do
  mem_usage="$(docker stats --no-stream --format '{{.MemUsage}}' "$container_name" 2>/dev/null | awk -F/ 'NR==1 {gsub(/^ +| +$/, "", $1); print $1}')"
  if [[ -n "$mem_usage" ]]; then
    mem_bytes="$(python3 - "$mem_usage" <<'PY'
import re
import sys

match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)([KMGTPE]?i?B)", sys.argv[1].strip())
if not match:
    raise SystemExit(1)
number = float(match.group(1))
unit = match.group(2)
scale = {
    "B": 1, "KB": 1000, "MB": 1000**2, "GB": 1000**3,
    "KiB": 1024, "MiB": 1024**2, "GiB": 1024**3,
}
print(int(number * scale[unit]))
PY
)"
    printf '%s\t%s\t%s\n' "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" "$mem_usage" "$mem_bytes" >>"$stats_log"
    if (( mem_bytes > peak_rss_bytes )); then
      peak_rss_bytes="$mem_bytes"
    fi
  fi
  sleep 1
done
wait "$docker_pid"
exit_code=$?
set -e
end_time="$(python3 -c 'import time; print(time.time())')"
wall_time_seconds="$(python3 -c "print(round($end_time - $start_time, 6))")"
if (( peak_rss_bytes > 0 )); then
  peak_rss_mb="$(python3 -c "print(round($peak_rss_bytes / 1024 / 1024, 3))")"
  peak_rss_status="recorded"
fi

export ISONCLUST3_REPORT_JSON="$report_json"
export ISONCLUST3_REPORT_TSV="$report_tsv"
export ISONCLUST3_MANIFEST_ID="$manifest_id"
export ISONCLUST3_BENCHMARK_TIER="$benchmark_tier"
export ISONCLUST3_PLATFORM="$platform"
export ISONCLUST3_IMAGE="$image"
export ISONCLUST3_CONTAINER_DIGEST="$container_digest"
export ISONCLUST3_FASTQ_HOST="$fastq_host"
export ISONCLUST3_FINAL_CLUSTERS="$run_out/clustering/final_clusters.tsv"
export ISONCLUST3_RUN_LOG="$run_log"
export ISONCLUST3_STATS_LOG="$stats_log"
export ISONCLUST3_WALL_TIME_SECONDS="$wall_time_seconds"
export ISONCLUST3_PEAK_RSS_MB="$peak_rss_mb"
export ISONCLUST3_PEAK_RSS_STATUS="$peak_rss_status"
export ISONCLUST3_THREAD_COUNT="$threads"
export ISONCLUST3_EXIT_CODE="$exit_code"
export ISONCLUST3_RUN_ID="$run_id"
export ISONCLUST3_COMMAND="${cmd[*]}"
export ISONCLUST3_HOST_OS="$(uname -s)"
export ISONCLUST3_HOST_ARCH="$(uname -m)"
export ISONCLUST3_MODE="$mode"
export ISONCLUST3_SEEDING="$seeding"

python3 <<'PY'
import csv
import hashlib
import json
import os
from pathlib import Path


def sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


final_clusters = Path(os.environ["ISONCLUST3_FINAL_CLUSTERS"])
outputs = []
final_checksum = sha256(final_clusters)
if final_checksum:
    outputs.append(
        {
            "role": "final_clusters",
            "path": str(final_clusters),
            "sha256": final_checksum,
        }
    )

exit_code = int(os.environ["ISONCLUST3_EXIT_CODE"])
contract_status = "accepted_contract" if exit_code == 0 and final_checksum else "rejected_contract"
report = {
    "schema_version": 1,
    "project": "isONclust3",
    "manifest_id": os.environ["ISONCLUST3_MANIFEST_ID"],
    "benchmark_tier": os.environ["ISONCLUST3_BENCHMARK_TIER"],
    "platform": os.environ["ISONCLUST3_PLATFORM"],
    "host_os": os.environ["ISONCLUST3_HOST_OS"],
    "cpu_architecture": os.environ["ISONCLUST3_HOST_ARCH"],
    "container_digest": os.environ["ISONCLUST3_CONTAINER_DIGEST"],
    "run_id": os.environ["ISONCLUST3_RUN_ID"],
    "mode": os.environ["ISONCLUST3_MODE"],
    "seeding": os.environ["ISONCLUST3_SEEDING"],
    "command": os.environ["ISONCLUST3_COMMAND"].split(),
    "exit_code": exit_code,
    "inputs": [
        {
            "role": "input_fastq",
            "path": os.environ["ISONCLUST3_FASTQ_HOST"],
            "sha256": sha256(Path(os.environ["ISONCLUST3_FASTQ_HOST"])),
        }
    ],
    "outputs": outputs,
    "metrics": {
        "wall_time_seconds": float(os.environ["ISONCLUST3_WALL_TIME_SECONDS"]),
        "peak_rss_mb": (
            float(os.environ["ISONCLUST3_PEAK_RSS_MB"])
            if os.environ["ISONCLUST3_PEAK_RSS_MB"]
            else None
        ),
        "peak_rss_status": os.environ["ISONCLUST3_PEAK_RSS_STATUS"],
        "thread_count": int(os.environ["ISONCLUST3_THREAD_COUNT"]),
    },
    "acceptance": {
        "contract": {"status": contract_status},
        "time_to_answer": {"status": "recorded"},
        "memory": {"status": os.environ["ISONCLUST3_PEAK_RSS_STATUS"]},
    },
    "log": os.environ["ISONCLUST3_RUN_LOG"],
    "stats_log": os.environ["ISONCLUST3_STATS_LOG"],
}

Path(os.environ["ISONCLUST3_REPORT_JSON"]).write_text(
    json.dumps(report, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
with Path(os.environ["ISONCLUST3_REPORT_TSV"]).open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(
        handle,
        fieldnames=[
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
        ],
        delimiter="\t",
    )
    writer.writeheader()
    writer.writerow(
        {
            "project": report["project"],
            "manifest_id": report["manifest_id"],
            "benchmark_tier": report["benchmark_tier"],
            "platform": report["platform"],
            "container_digest": report["container_digest"],
            "wall_time_seconds": report["metrics"]["wall_time_seconds"],
            "peak_rss_mb": report["metrics"]["peak_rss_mb"],
            "thread_count": report["metrics"]["thread_count"],
            "contract_status": contract_status,
            "final_clusters_sha256": final_checksum or "",
        }
    )
PY

echo "wrote $report_json"
echo "wrote $report_tsv"
exit "$exit_code"
