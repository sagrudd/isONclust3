# isONclust3 Blocker Register

This register tracks release blockers for the maintained `sagrudd/isONclust3`
fork before `newONform` can cite its generated cluster tables as accepted
upstream evidence.

| ID | Area | Blocker | Required Resolution |
| --- | --- | --- | --- |
| ISOCLUST-BLOCK-001 | GB10 evidence | Dockerized GB10 reports have not been collected for medium ONT or Phanerognostikon-scale ONT workloads. Toy ONT and toy PacBio GB10 contract reports are accepted for source commit `3ba608e3fa87d855f11d75e3c77556f2dd6b1a59` and are archived outside Git. | Run `scripts/run-gb10-benchmark.sh` for each accepted larger-workload manifest on GB10 and archive JSON/TSV reports outside Git. |
| ISOCLUST-BLOCK-002 | Generated inputs | Medium and Phanerognostikon-scale `final_clusters.tsv` outputs do not yet have accepted producer checksums for `newONform`. | Generate cluster tables with the accepted container image, record input and output checksums, and update `newONform` generated-input registers. |
| ISOCLUST-BLOCK-003 | Performance profile | Local toy profiling automation and optimization ranking now exist, but seed extraction, clustering merge bookkeeping, cluster FASTQ output, and GFF-assisted clustering have not yet been profiled on accepted larger workloads. | Use `scripts/run-local-profiling.sh` for toy before/after checks, then rank larger-workload wall time, peak RSS, mode, read count, and output-risk notes before algorithmic changes. |
## Resolved Blockers

- Strict `cargo fmt --check`, `cargo test`, and `cargo clippy --all-targets -- -D warnings`
  pass for the current crate surface.
- Tiny ONT and PacBio output-contract fixtures regenerate deterministic
  `final_clusters.tsv` outputs and verify expected checksums.
- `ISOCLUST-BLOCK-004`: `newONform` directly consumes committed tiny ONT and
  PacBio `isONclust3` `final_clusters.tsv` fixtures without transformation.
- Local profiling automation and the static optimization ranking are tracked in
  `PERFORMANCE_DEEP_DIVE.md`; they do not resolve GB10 evidence requirements.
- Toy ONT and toy PacBio GB10 contract reports are accepted under
  `/home/stephen/gb10-verification-20260704/results/isONclust3-provenance/`
  with source commit, tool version, image digest, command, checksums, wall
  time, peak RSS, CPU architecture, and thread count recorded.

## Waiver Rules

- Waivers must name the blocker ID, affected workload, evidence available,
  downstream `newONform` impact, and expiry condition.
- A waiver narrows release scope; it does not claim accepted GB10 producer
  evidence or generated `final_clusters.tsv` checksum readiness.
- Release notes and the downstream `newONform` release train must list active
  waivers before any waived producer output is cited.
