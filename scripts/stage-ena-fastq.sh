#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Stage an ENA FASTQ for isONclust3 GB10 evidence.

Required:
  --uri URI             ENA/FTP/HTTPS FASTQ URI.
  --md5 HEX            Expected MD5 for the downloaded compressed file.
  --output-dir DIR     Directory where reads.fastq and checksums are written.

Optional:
  --compressed-name N  Download filename. Default: basename of URI.
  --fastq-name N       Decompressed FASTQ filename. Default: reads.fastq.
  -h, --help           Show this help.

The script downloads or reuses the compressed FASTQ, verifies its MD5, writes a
plain FASTQ for the isONclust3 runner, and records SHA-256/byte metadata. Keep
the output directory outside the repository; raw sequencing data must not be
committed.
USAGE
}

uri=""
expected_md5=""
output_dir=""
compressed_name=""
fastq_name="reads.fastq"

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
    --uri) require_value "$1" "${2:-}"; uri="$2"; shift 2 ;;
    --md5) require_value "$1" "${2:-}"; expected_md5="$2"; shift 2 ;;
    --output-dir) require_value "$1" "${2:-}"; output_dir="$2"; shift 2 ;;
    --compressed-name) require_value "$1" "${2:-}"; compressed_name="$2"; shift 2 ;;
    --fastq-name) require_value "$1" "${2:-}"; fastq_name="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

if [[ -z "$uri" || -z "$expected_md5" || -z "$output_dir" ]]; then
  echo "--uri, --md5, and --output-dir are required" >&2
  usage >&2
  exit 2
fi
if [[ ! "$expected_md5" =~ ^[0-9a-fA-F]{32}$ ]]; then
  echo "--md5 must be 32 hexadecimal characters" >&2
  exit 2
fi
if [[ -z "$compressed_name" ]]; then
  compressed_name="$(basename "$uri")"
fi

mkdir -p "$output_dir"
output_dir="$(cd "$output_dir" && pwd)"
compressed_path="$output_dir/$compressed_name"
fastq_path="$output_dir/$fastq_name"
metadata_json="$output_dir/staging-checksums.json"
metadata_tsv="$output_dir/staging-checksums.tsv"

if [[ ! -s "$compressed_path" ]]; then
  curl --fail --location --continue-at - --output "$compressed_path" "$uri"
fi

observed_md5="$(
  python3 - "$compressed_path" <<'PY'
import hashlib
import sys
from pathlib import Path

path = Path(sys.argv[1])
digest = hashlib.md5()
with path.open("rb") as handle:
    for chunk in iter(lambda: handle.read(1024 * 1024), b""):
        digest.update(chunk)
print(digest.hexdigest())
PY
)"
expected_md5="$(printf '%s' "$expected_md5" | tr '[:upper:]' '[:lower:]')"
if [[ "$observed_md5" != "$expected_md5" ]]; then
  echo "MD5 mismatch for $compressed_path: $observed_md5 != $expected_md5" >&2
  exit 1
fi

case "$compressed_path" in
  *.gz)
    gzip -dc "$compressed_path" >"$fastq_path"
    ;;
  *)
    cp "$compressed_path" "$fastq_path"
    ;;
esac

python3 - "$uri" "$compressed_path" "$fastq_path" "$metadata_json" "$metadata_tsv" <<'PY'
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


uri = sys.argv[1]
compressed = Path(sys.argv[2])
fastq = Path(sys.argv[3])
metadata_json = Path(sys.argv[4])
metadata_tsv = Path(sys.argv[5])
record = {
    "uri": uri,
    "compressed_path": str(compressed),
    "compressed_bytes": compressed.stat().st_size,
    "compressed_sha256": sha256(compressed),
    "fastq_path": str(fastq),
    "fastq_bytes": fastq.stat().st_size,
    "fastq_sha256": sha256(fastq),
}
metadata_json.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
with metadata_tsv.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=record.keys(), delimiter="\t")
    writer.writeheader()
    writer.writerow(record)
print(json.dumps(record, indent=2, sort_keys=True))
PY
