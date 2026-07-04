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
- Dockerized benchmark runner, toy ONT/PacBio manifests, accepted medium and
  Phanerognostikon-scale manifests, and local Docker toy smoke automation.
- Local profiling harness and optimization evidence ledger for behavior
  preserving performance work.
- Release preflight validation for governance files, blocker visibility,
  benchmark acceptance markers, TODO evidence markers, file-size limits,
  manifest checksums, Sphinx documentation build markers, CI markers, and
  tracked-artifact hygiene.

## Evidence Required Before RC Acceptance

- Accepted GB10 benchmark reports for toy ONT, toy PacBio, and medium ONT are
  recorded; Phanerognostikon-scale ONT remains required.
- Container image identity, command lines, input checksums, generated
  output checksums, generated `final_clusters.tsv` checksums, wall time, peak
  RSS, CPU architecture, and thread count for each accepted run.
- Accepted Phanerognostikon generated `final_clusters.tsv` producer checksums
  for `newONform` release evidence. Medium DRR138512 is accepted with checksum
  `a37798b916ba5078ca90bed40946ad694bbae957d724034a51e040689406acc7`.
- Larger-workload profiling evidence for seed generation, minimizer/syncmer
  extraction, clustering bookkeeping, cluster FASTQ output, and GFF-assisted
  paths before further algorithmic optimization claims.
- Matching `newONform` submodule, generated-input register, blocker, and
  documentation updates in the same release train.

## Known Limits

- `ISOCLUST-BLOCK-001`: Phanerognostikon GB10 producer evidence is accepted
  and archived outside Git for DRR178488.
- `ISOCLUST-BLOCK-002`: the generated Phanerognostikon `final_clusters.tsv`
  output has an accepted producer checksum for downstream `newONform`.
- `ISOCLUST-BLOCK-003`: accepted larger-workload profiling evidence is still
  pending.
- Local toy profiling and Docker smoke automation are readiness gates, not
  GB10 release evidence.

## Operator Notes

Use `BLOCKERS.md`, `BENCHMARK_ACCEPTANCE.md`, and `RELEASE_CHECKLIST.md` as the
release gate. Waivers must stay visible as scoped release limitations and do
not claim accepted GB10 producer evidence or generated `final_clusters.tsv`
checksum readiness for `newONform`. Do not tag a release candidate from this draft alone.
