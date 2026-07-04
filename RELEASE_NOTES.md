# isONclust3 0.3.0-rc Planning Draft

This draft records the maintained `sagrudd/isONclust3` release-candidate scope.
It is not a release announcement while accepted larger-workload profiling
evidence remains pending under `ISOCLUST-BLOCK-003`.

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

- Accepted GB10 benchmark reports for toy ONT, toy PacBio, medium ONT, and
  Phanerognostikon-scale ONT are recorded.
- Current-source GB10 Docker toy smoke evidence for commit
  `aa494f6b6ae9a5ce99fd889b90328941553ef2a5` is archived under
  `/home/stephen/gb10-verification-20260704/results/isONclust3-aa494f6-docker-toy-smoke/`.
- Container image identity, command lines, input checksums, generated
  output checksums, generated `final_clusters.tsv` checksums, wall time, peak
  RSS, CPU architecture, and thread count for each accepted run.
- Accepted Phanerognostikon generated `final_clusters.tsv` producer checksums
  for `newONform` release evidence. Medium DRR138512 is accepted with checksum
  `a37798b916ba5078ca90bed40946ad694bbae957d724034a51e040689406acc7`.
- Larger-workload profiling evidence for GFF-assisted paths before further
  algorithmic optimization claims. Default medium DRR138512
  seed-generation/minimizer-extraction and write-FASTQ output profiling is
  recorded outside Git; medium post-cluster profiling is rejected for handoff
  compatibility because it changes `final_clusters.tsv`.
- Matching `newONform` submodule, generated-input register, blocker, and
  documentation updates in the same release train.

## Known Limits

- `ISOCLUST-BLOCK-001`: Phanerognostikon GB10 producer evidence is accepted
  and archived outside Git for DRR178488.
- `ISOCLUST-BLOCK-002`: the generated Phanerognostikon `final_clusters.tsv`
  output has an accepted producer checksum for downstream `newONform`.
- `ISOCLUST-BLOCK-003`: accepted larger-workload profiling evidence is still
  pending for GFF-assisted paths; post-cluster medium evidence is rejected for
  handoff compatibility.
- Medium DRR138512 default-path profiling is archived under
  `/home/stephen/gb10-verification-20260704/results/isONclust3-larger-profile-drr138512-7a3f390/`
  with exit code 0, 161.454274 seconds wall time, 2161.68 MiB peak RSS, exact
  final-clusters contract match, and checksum
  `a37798b916ba5078ca90bed40946ad694bbae957d724034a51e040689406acc7`.
- Medium DRR138512 write-FASTQ profiling is archived under
  `/home/stephen/gb10-verification-20260704/results/isONclust3-larger-profile-drr138512-313a7f7-write-fastq/`
  with exit code 0, 186.226314 seconds wall time, 2162.18 MiB peak RSS, exact
  final-clusters contract match, and checksum
  `a37798b916ba5078ca90bed40946ad694bbae957d724034a51e040689406acc7`.
- Medium DRR138512 post-cluster profiling is archived under
  `/home/stephen/gb10-verification-20260704/results/isONclust3-larger-profile-drr138512-7c29eec-post-cluster/`
  with process exit code 0, 438.801846 seconds wall time, 2161.395 MiB peak RSS,
  but `final_clusters.tsv` changed to
  `cab07475f8e3559187191f86f50a5c7534658ad960cb881dd837b5305f3ad547`; this is
  rejected handoff evidence, not accepted contract evidence.
- Tiny ONT GFF-assisted GB10 harness smoke is archived under
  `/home/stephen/gb10-verification-20260704/results/isONclust3-gff-harness-smoke-2a859a1/`
  with exit code 0, 0.003554 seconds wall time, 15.246 MiB peak RSS, exact
  final-clusters contract match, and checksum
  `e28ef900515871b0da07f0f10a2bccc7d35323b087ffd4633878bb372ada2538`; this
  verifies the harness interface only and is not accepted larger-workload GFF
  evidence.
- Local toy profiling and Docker smoke automation are readiness gates, not
  GB10 release evidence.

## Operator Notes

Use `BLOCKERS.md`, `BENCHMARK_ACCEPTANCE.md`, and `RELEASE_CHECKLIST.md` as the
release gate. Waivers must stay visible as scoped release limitations and do
not claim accepted GB10 producer evidence or generated `final_clusters.tsv`
checksum readiness for `newONform`. Do not tag a release candidate from this draft alone.
