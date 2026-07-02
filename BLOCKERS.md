# isONclust3 Blocker Register

This register tracks release blockers for the maintained `sagrudd/isONclust3`
fork before `newONform` can cite its generated cluster tables as accepted
upstream evidence.

| ID | Area | Blocker | Required Resolution |
| --- | --- | --- | --- |
| ISOCLUST-BLOCK-001 | GB10 evidence | Dockerized GB10 reports have not been collected for toy ONT, toy PacBio, medium ONT, or Phanerognostikon-scale ONT workloads. | Run `scripts/run-gb10-benchmark.sh` for each accepted manifest on GB10 and archive JSON/TSV reports outside Git. |
| ISOCLUST-BLOCK-002 | Generated inputs | Medium and Phanerognostikon-scale `final_clusters.tsv` outputs do not yet have accepted producer checksums for `newONform`. | Generate cluster tables with the accepted container image, record input and output checksums, and update `newONform` generated-input registers. |
| ISOCLUST-BLOCK-003 | Performance profile | Seed extraction, clustering merge bookkeeping, and cluster FASTQ output have not been profiled independently. | Rank optimization targets with wall time, peak RSS, mode, read count, and output-risk notes before algorithmic changes. |
| ISOCLUST-BLOCK-004 | Downstream consumer fixture | `newONform` does not yet consume committed `isONclust3` fixture output as a release preflight fixture. | Add a `newONform` fixture that reads committed `isONclust3` `final_clusters.tsv` output without transformation. |

## Resolved Blockers

- Strict `cargo fmt --check`, `cargo test`, and `cargo clippy --all-targets -- -D warnings`
  pass for the current crate surface.
- Tiny ONT and PacBio output-contract fixtures regenerate deterministic
  `final_clusters.tsv` outputs and verify expected checksums.
