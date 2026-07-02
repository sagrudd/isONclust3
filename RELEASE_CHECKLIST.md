# isONclust3 Release Checklist

Use this checklist before a release-candidate tag or before updating
`newONform` to cite `isONclust3` producer evidence.

## Required Local Checks

- [ ] `cargo fmt --check`
- [ ] `cargo test --quiet`
- [ ] `cargo clippy --all-targets -- -D warnings`
- [ ] `scripts/check-output-contract-fixtures.sh`
- [ ] `scripts/run-local-profiling.sh --case all`
- [ ] `scripts/release-preflight.py --expected-version 0.3.0`
- [ ] `scripts/check-docker-toy-benchmarks.sh`
- [ ] `git diff --check`

## Required Docker And GB10 Evidence

- [ ] Build the benchmark image from a clean checkout.
- [ ] Run toy ONT and toy PacBio manifests through
      `scripts/check-docker-toy-benchmarks.sh`.
- [ ] Run accepted medium ONT and Phanerognostikon-scale ONT manifests on GB10.
- [ ] Capture JSON and TSV reports with image identity, command, input checksums,
      output checksums, wall time, peak RSS, CPU architecture, and thread count.
- [ ] Store bulky reports and generated outputs outside Git.

## Required Integration Evidence

- [ ] Confirm `OUTPUT_CONTRACTS.md` still matches emitted
      `clustering/final_clusters.tsv`.
- [ ] Publish accepted `final_clusters.tsv` checksums for every generated
      `newONform` benchmark input.
- [ ] Update `newONform` submodule, generated-input registers, release notes,
      blockers, and Sphinx documentation in the same release train.
- [ ] Confirm unresolved gates remain listed in `BLOCKERS.md`.
