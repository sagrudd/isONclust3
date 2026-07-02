# isONclust3 0.3.0-rc Planning Draft

This draft records the maintained `sagrudd/isONclust3` release-candidate scope.
It is not a release announcement until Dockerized GB10 producer evidence and
downstream generated-input checksums are complete.

## Intended Scope

- Maintained fork of `isONclust3` for the upstream clustering stage used by
  `newONform` transcriptome consolidation.
- Preserved `final_clusters.tsv` handoff contract with tiny ONT and PacBio
  checksum-backed output fixtures.
- Strict `cargo fmt --check`, `cargo test --quiet`, and
  `cargo clippy --all-targets -- -D warnings` hygiene for the current crate
  surface.
- Dockerized benchmark runner, toy ONT/PacBio manifests, pending medium and
  Phanerognostikon-scale manifests, and local Docker toy smoke automation.
- Local profiling harness and optimization evidence ledger for behavior
  preserving performance work.
- Release preflight validation for governance files, blocker visibility,
  benchmark acceptance markers, TODO evidence markers, file-size limits,
  manifest checksums, CI markers, and tracked-artifact hygiene.

## Evidence Required Before RC Acceptance

- Accepted GB10 benchmark reports for toy ONT, toy PacBio, medium ONT, and
  Phanerognostikon-scale ONT workloads.
- Container image identity, command lines, input checksums, generated
  output checksums, generated `final_clusters.tsv` checksums, wall time, peak
  RSS, CPU architecture, and thread count for each accepted run.
- Accepted medium and Phanerognostikon generated `final_clusters.tsv` producer
  checksums for `newONform` release evidence.
- Larger-workload profiling evidence for seed generation, minimizer/syncmer
  extraction, clustering bookkeeping, cluster FASTQ output, and GFF-assisted
  paths before further algorithmic optimization claims.
- Matching `newONform` submodule, generated-input register, blocker, and
  documentation updates in the same release train.

## Known Limits

- `ISOCLUST-BLOCK-001`: accepted GB10 benchmark reports have not yet been
  collected.
- `ISOCLUST-BLOCK-002`: generated medium and Phanerognostikon
  `final_clusters.tsv` outputs do not yet have accepted producer checksums.
- `ISOCLUST-BLOCK-003`: accepted larger-workload profiling evidence is still
  pending.
- Local toy profiling and Docker smoke automation are readiness gates, not
  GB10 release evidence.

## Operator Notes

Use `BLOCKERS.md`, `BENCHMARK_ACCEPTANCE.md`, and `RELEASE_CHECKLIST.md` as the
release gate. Do not tag a release candidate from this draft alone.
