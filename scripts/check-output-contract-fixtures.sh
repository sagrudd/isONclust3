#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmp_root="$(mktemp -d "${TMPDIR:-/tmp}/isonclust3-contract.XXXXXX")"
trap 'rm -rf "$tmp_root"' EXIT

run_fixture() {
  local mode="$1"
  local name="$2"
  local fixture_dir="$repo_root/fixtures/tiny/$name"
  local out_dir="$tmp_root/$name"

  (cd "$fixture_dir" && sha256sum -c checksums.sha256)

  cargo run --quiet --manifest-path "$repo_root/Cargo.toml" -- \
    --fastq "$fixture_dir/reads.fastq" \
    --mode "$mode" \
    --outfolder "$out_dir" \
    --seeding minimizer \
    --no-fastq

  cmp \
    "$fixture_dir/expected/final_clusters.tsv" \
    "$out_dir/clustering/final_clusters.tsv"

  cargo run --quiet --manifest-path "$repo_root/Cargo.toml" -- \
    --fastq "$fixture_dir/reads.fastq" \
    --mode "$mode" \
    --outfolder "$out_dir-gff" \
    --seeding minimizer \
    --no-fastq \
    --init-cl "$fixture_dir/reference.fasta" \
    --gff "$fixture_dir/annotation.gff3"

  cmp \
    "$fixture_dir/expected/gff_final_clusters.tsv" \
    "$out_dir-gff/clustering/final_clusters.tsv"
}

run_fixture ont ont
run_fixture pacbio pacbio
