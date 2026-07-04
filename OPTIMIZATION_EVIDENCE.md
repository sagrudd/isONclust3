# isONclust3 Optimization Evidence

This ledger records local before/after evidence for algorithmic optimization
commits in the maintained `sagrudd/isONclust3` fork. It is not GB10 release
evidence. Raw local reports must not be committed; keep them under
`target/local-profile/` or another ignored location and cite their paths here.

Accepted release evidence still requires Dockerized GB10 reports, accepted
medium and Phanerognostikon-scale input checksums, and resolved blocker status
for `ISOCLUST-BLOCK-001`, `ISOCLUST-BLOCK-002`, and `ISOCLUST-BLOCK-003`.

## Required Entry Fields

Every algorithmic optimization entry should include:

- commit SHA and date
- optimized facet
- compatibility risk for `clustering/final_clusters.tsv`
- before command and ignored report path
- after command and ignored report path
- contract checks run
- GB10 or larger-workload status

Use the full local profiling gate when the changed path can affect clustering,
FASTQ output, post-clustering, or GFF-assisted initialization:

```sh
scripts/run-local-profiling.sh --case all --include-fastq-output --include-post-cluster --include-gff
```

## Entries

### ae1c21151eb6cb2e6b962130a72c955e406a116d - Stream cluster FASTQ output

- Date: 2026-07-02
- Optimized facet: per-cluster FASTQ output materialization in
  `src/write_output.rs`.
- Compatibility risk: low for the `newONform` handoff because
  `clustering/final_clusters.tsv` generation was intentionally unchanged;
  medium for users relying on emitted per-cluster FASTQ files.
- Before command:
  `scripts/run-local-profiling.sh --case all --include-fastq-output --include-post-cluster --include-gff`
- Before report path: `target/local-profile/` from the pre-change tree.
- After command:
  `scripts/run-local-profiling.sh --case all --include-fastq-output --include-post-cluster --include-gff`
- After report path: `target/local-profile/` from the post-change tree.
- Contract checks run:
  `cargo fmt --check`, `cargo test --quiet`,
  `cargo clippy --all-targets -- -D warnings`,
  `scripts/check-output-contract-fixtures.sh`,
  `scripts/release-preflight.py --expected-version 0.3.0`, and
  `git diff --check`.
- GB10 or larger-workload status: local toy evidence only. Do not mark
  `ISOCLUST-BLOCK-001`, `ISOCLUST-BLOCK-002`, or `ISOCLUST-BLOCK-003`
  resolved from this entry.

### 60418948dce8ccd71d8da700584944cfbb4ab910 - Name post-cluster merge candidates

- Date: 2026-07-02
- Optimized facet: post-clustering merge bookkeeping readability and review
  safety in `src/clustering.rs`.
- Compatibility risk: high because post-clustering merge behavior can affect
  cluster membership; accepted only with exact output-contract fixture checks.
- Before command:
  `scripts/run-local-profiling.sh --case all --include-post-cluster`
- Before report path: `target/local-profile/` from the pre-change tree.
- After command:
  `scripts/run-local-profiling.sh --case all --include-post-cluster`
- After report path: `target/local-profile/` from the post-change tree.
- Contract checks run:
  `cargo fmt --check`, `cargo test --quiet`,
  `cargo clippy --all-targets -- -D warnings`,
  `scripts/check-output-contract-fixtures.sh`, and
  `scripts/release-preflight.py --expected-version 0.3.0`.
- GB10 or larger-workload status: local toy evidence only; larger-workload
  profiling remains blocked pending accepted input access and checksums.

### 152da1023cba096785bf810eb26c4f256a89a6d7 - Use fixed PHRED count storage

- Date: 2026-07-02
- Optimized facet: FASTQ sorting quality-score storage in
  `src/generate_sorted_fastq_for_cluster.rs`.
- Compatibility risk: medium because sorting order can affect cluster IDs and
  therefore `clustering/final_clusters.tsv` ordering.
- Before command:
  `scripts/run-local-profiling.sh --case all`
- Before report path: `target/local-profile/` from the pre-change tree.
- After command:
  `scripts/run-local-profiling.sh --case all`
- After report path: `target/local-profile/` from the post-change tree.
- Contract checks run:
  `cargo fmt --check`, `cargo test --quiet`,
  `cargo clippy --all-targets -- -D warnings`,
  `scripts/check-output-contract-fixtures.sh`, and
  `scripts/release-preflight.py --expected-version 0.3.0`.
- GB10 or larger-workload status: local toy profiling evidence only; accepted
  GB10 producer reports are recorded separately for toy, medium, and
  Phanerognostikon workloads and do not by themselves resolve
  `ISOCLUST-BLOCK-003`.
