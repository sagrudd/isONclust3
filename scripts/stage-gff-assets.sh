#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Stage reference FASTA and GFF3 assets for isONclust3 GFF-assisted profiling.

Required:
  --reference URI_OR_FILE      Reference FASTA source.
  --annotation URI_OR_FILE     GFF3 annotation source.
  --output-dir DIR            Directory where staged assets and metadata go.

Optional:
  --reference-sha256 HEX      Expected SHA-256 for the staged reference FASTA.
  --annotation-sha256 HEX     Expected SHA-256 for the staged annotation GFF3.
  --reference-name NAME       Staged reference filename. Default: reference.fasta.
  --annotation-name NAME      Staged annotation filename. Default: annotation.gff3.
  -h, --help                  Show this help.

Sources may be local files or HTTP(S)/FTP URLs. If a source filename ends in
.gz, the script writes the decompressed file for --init-cl/--gff use. Keep the
output directory outside the repository; reference and annotation assets for
larger workloads must not be committed.
USAGE
}

reference_source=""
annotation_source=""
output_dir=""
reference_sha256=""
annotation_sha256=""
reference_name="reference.fasta"
annotation_name="annotation.gff3"

require_value() {
  local option="$1"
  local value="${2:-}"
  if [[ -z "$value" || "$value" == --* ]]; then
    echo "$option requires a value" >&2
    usage >&2
    exit 2
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --reference) require_value "$1" "${2:-}"; reference_source="$2"; shift 2 ;;
    --annotation) require_value "$1" "${2:-}"; annotation_source="$2"; shift 2 ;;
    --output-dir) require_value "$1" "${2:-}"; output_dir="$2"; shift 2 ;;
    --reference-sha256) require_value "$1" "${2:-}"; reference_sha256="$2"; shift 2 ;;
    --annotation-sha256) require_value "$1" "${2:-}"; annotation_sha256="$2"; shift 2 ;;
    --reference-name) require_value "$1" "${2:-}"; reference_name="$2"; shift 2 ;;
    --annotation-name) require_value "$1" "${2:-}"; annotation_name="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

if [[ -z "$reference_source" || -z "$annotation_source" || -z "$output_dir" ]]; then
  echo "--reference, --annotation, and --output-dir are required" >&2
  usage >&2
  exit 2
fi
if [[ -n "$reference_sha256" && ! "$reference_sha256" =~ ^[0-9a-fA-F]{64}$ ]]; then
  echo "--reference-sha256 must be 64 hexadecimal characters" >&2
  exit 2
fi
if [[ -n "$annotation_sha256" && ! "$annotation_sha256" =~ ^[0-9a-fA-F]{64}$ ]]; then
  echo "--annotation-sha256 must be 64 hexadecimal characters" >&2
  exit 2
fi

mkdir -p "$output_dir"
output_dir="$(cd "$output_dir" && pwd)"
download_dir="$output_dir/downloads"
mkdir -p "$download_dir"

metadata_json="$output_dir/gff-asset-checksums.json"
metadata_tsv="$output_dir/gff-asset-checksums.tsv"
reference_path="$output_dir/$reference_name"
annotation_path="$output_dir/$annotation_name"

fetch_source() {
  local source="$1"
  local destination="$2"
  case "$source" in
    http://*|https://*|ftp://*)
      if [[ ! -s "$destination" ]]; then
        curl --fail --location --continue-at - --output "$destination" "$source"
      fi
      ;;
    *)
      if [[ ! -f "$source" ]]; then
        echo "missing local source: $source" >&2
        exit 2
      fi
      cp "$source" "$destination"
      ;;
  esac
}

stage_plain() {
  local source="$1"
  local output="$2"
  local downloaded="$3"
  fetch_source "$source" "$downloaded"
  case "$downloaded" in
    *.gz)
      gzip -dc "$downloaded" >"$output"
      ;;
    *)
      cp "$downloaded" "$output"
      ;;
  esac
}

reference_download="$download_dir/$(basename "$reference_source")"
annotation_download="$download_dir/$(basename "$annotation_source")"
stage_plain "$reference_source" "$reference_path" "$reference_download"
stage_plain "$annotation_source" "$annotation_path" "$annotation_download"

python3 - \
  "$reference_source" \
  "$annotation_source" \
  "$reference_path" \
  "$annotation_path" \
  "$reference_sha256" \
  "$annotation_sha256" \
  "$metadata_json" \
  "$metadata_tsv" <<'PY'
import csv
import hashlib
import json
import sys
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


reference_source = sys.argv[1]
annotation_source = sys.argv[2]
reference_path = Path(sys.argv[3])
annotation_path = Path(sys.argv[4])
expected_reference_sha = sys.argv[5].lower()
expected_annotation_sha = sys.argv[6].lower()
metadata_json = Path(sys.argv[7])
metadata_tsv = Path(sys.argv[8])

reference_sha = sha256(reference_path)
annotation_sha = sha256(annotation_path)
if expected_reference_sha and reference_sha != expected_reference_sha:
    raise SystemExit(
        f"reference SHA-256 mismatch: {reference_sha} != {expected_reference_sha}"
    )
if expected_annotation_sha and annotation_sha != expected_annotation_sha:
    raise SystemExit(
        f"annotation SHA-256 mismatch: {annotation_sha} != {expected_annotation_sha}"
    )

records = [
    {
        "role": "reference_fasta",
        "source": reference_source,
        "path": str(reference_path),
        "bytes": reference_path.stat().st_size,
        "sha256": reference_sha,
    },
    {
        "role": "annotation_gff3",
        "source": annotation_source,
        "path": str(annotation_path),
        "bytes": annotation_path.stat().st_size,
        "sha256": annotation_sha,
    },
]
metadata_json.write_text(json.dumps(records, indent=2, sort_keys=True) + "\n", encoding="utf-8")
with metadata_tsv.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=records[0].keys(), delimiter="\t")
    writer.writeheader()
    writer.writerows(records)
print(json.dumps(records, indent=2, sort_keys=True))
PY
