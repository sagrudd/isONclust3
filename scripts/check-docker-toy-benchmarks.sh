#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Build or reuse the isONclust3 benchmark image and run tiny ONT/PacBio Docker
smokes through scripts/run-gb10-benchmark.sh.

Options:
  --image IMAGE        Image tag to build or reuse. Default: isonclust3:gb10-toy.
  --platform PLATFORM  Docker platform. Default: linux/arm64.
  --output-dir DIR     Keep reports under DIR instead of a temporary directory.
  --skip-build         Reuse an existing image tag.
  -h, --help           Show this help.
USAGE
}

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
image="isonclust3:gb10-toy"
platform="linux/arm64"
output_dir=""
skip_build="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --image)
      image="$2"
      shift 2
      ;;
    --platform)
      platform="$2"
      shift 2
      ;;
    --output-dir)
      output_dir="$2"
      shift 2
      ;;
    --skip-build)
      skip_build="true"
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

tmp_root=""
if [[ -z "$output_dir" ]]; then
  tmp_root="$(mktemp -d "${TMPDIR:-/tmp}/isonclust3-docker-toy.XXXXXX")"
  output_dir="$tmp_root"
  trap 'rm -rf "$tmp_root"' EXIT
else
  mkdir -p "$output_dir"
fi

if [[ "$skip_build" != "true" ]]; then
  docker build --platform "$platform" -t "$image" "$repo_root"
fi

run_and_compare() {
  local name="$1"
  local manifest="$repo_root/fixtures/manifests/tiny-$name.json"
  local input_dir="$repo_root/fixtures/tiny/$name"
  local expected="$input_dir/expected/final_clusters.tsv"
  local run_dir="$output_dir/$name"

  rm -rf "$run_dir"
  mkdir -p "$run_dir"

  "$repo_root/scripts/run-gb10-benchmark.sh" \
    --manifest "$manifest" \
    --input-dir "$input_dir" \
    --output-dir "$run_dir" \
    --image "$image" \
    --platform "$platform" \
    --run-id "local-toy-$name"

  cmp "$expected" "$run_dir/isonclust3/clustering/final_clusters.tsv"
}

run_and_compare ont
run_and_compare pacbio

echo "docker toy benchmark smoke passed: $output_dir"
