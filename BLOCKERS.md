# isONclust3 Blocker Register

This register tracks release blockers for the maintained `sagrudd/isONclust3`
fork before `newONform` can cite its generated cluster tables as accepted
upstream evidence.

| ID | Area | Blocker | Required Resolution |
| --- | --- | --- | --- |
| ISOCLUST-BLOCK-003 | Performance profile | Local toy profiling automation, optimization ranking, and medium DRR138512 default plus write-FASTQ larger-workload profiling now exist, but post-cluster merge bookkeeping and GFF-assisted clustering have not yet been profiled on accepted larger workloads. | Use `scripts/run-local-profiling.sh` for toy before/after checks and `scripts/run-larger-workload-profiling.sh` for accepted larger workloads, then rank larger-workload wall time, peak RSS, mode, read count, and output-risk notes before algorithmic changes. |
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
- Medium DRR138512 ONT GB10 contract evidence is accepted under
  `/home/stephen/gb10-verification-20260704/results/isONclust3-medium-drr138512/`
  for source commit `8ca0a8ddb8a7250765cb3e6b11e8463c476196b6`, tool version
  `0.3.0`, final cluster checksum
  `a37798b916ba5078ca90bed40946ad694bbae957d724034a51e040689406acc7`, and
  16,380,513 output bytes.
- `ISOCLUST-BLOCK-001`: Phanerognostikon DRR178488 ONT GB10 contract evidence
  is accepted under
  `/home/stephen/gb10-verification-20260704/results/isONclust3-phanerognostikon-drr178488-producer-e5d63a8/`
  for source commit `e5d63a87a8a265166e606e525e12f6c0aab7a7c5`, tool version
  `0.3.0`, wall time 6313.03955 seconds, and peak RSS 15544.32 MiB.
- `ISOCLUST-BLOCK-002`: the Phanerognostikon `final_clusters.tsv` producer
  checksum is accepted for downstream `newONform` handoff:
  `08a627f907ca387edae66fad9f5384a55d7a7228377bf3d8669a4f2d041f211c`
  with 104,692,828 output bytes.

## Waiver Rules

- Waivers must name the blocker ID, affected workload, evidence available,
  downstream `newONform` impact, and expiry condition.
- A waiver narrows release scope; it does not claim accepted GB10 producer
  evidence or generated `final_clusters.tsv` checksum readiness.
- Release notes and the downstream `newONform` release train must list active
  waivers before any waived producer output is cited.
