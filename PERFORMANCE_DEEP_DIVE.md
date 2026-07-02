# isONclust3 Performance Deep Dive

This document ranks optimization work for the maintained `sagrudd/isONclust3`
fork. It is a planning and local-profiling gate, not GB10 release evidence.
Accepted release evidence still requires Dockerized GB10 reports.

## Profiling Harness

Run local toy profiling with:

```sh
scripts/run-local-profiling.sh --output-dir target/local-profile
```

The harness builds the release binary, runs the tiny ONT and PacBio fixtures,
records wall time, peak resident set size when the host exposes it, input and
`final_clusters.tsv` checksums, and exact contract-match status against the
committed expected outputs. Reports are written under `target/` by default and
must not be committed.

Use `--include-fastq-output` when profiling per-cluster FASTQ materialization,
and `--include-post-cluster` when profiling merge refinement behavior. These
variants are intentionally opt-in because they measure different code paths
than the default `newONform` handoff, which uses `--no-fastq`.

## Ranked Facets

1. Seed extraction and filtering in the sorting pass.
   - Primary files: `src/generate_sorted_fastq_for_cluster.rs`,
     `src/seeding_and_filtering_seeds.rs`.
   - Why it matters: each read builds a fresh `Vec<MinimizerHashed>` and then
     filters it before sorting reads by high-confidence seed count.
   - Measurement: compare ONT and PacBio local profiling reports with default
     `--no-fastq`, then repeat on the smallest accepted larger workload before
     changing allocation behavior.
   - Output risk: medium. The sorted read order influences cluster IDs and
     therefore `final_clusters.tsv` ordering.

2. Seed extraction and cluster assignment in the clustering pass.
   - Primary files: `src/main.rs`, `src/clustering.rs`,
     `src/seeding_and_filtering_seeds.rs`.
   - Why it matters: seeds are recomputed for each sorted read, and shared-seed
     vectors are rebuilt against the current cluster map.
   - Measurement: compare profiling reports before and after any shared seed
     generation helper, with exact `final_clusters.tsv` fixture comparison.
   - Output risk: high. Assignment changes can alter cluster membership.

3. Post-clustering merge bookkeeping.
   - Primary files: `src/clustering.rs`.
   - Why it matters: merge refinement mutates cluster and seed maps while
     tracking shared-seed counts; tuple-like state makes optimization risk hard
     to review.
   - Measurement: run `scripts/run-local-profiling.sh --include-post-cluster`
     before changing data structures, then repeat with a larger workload.
   - Output risk: high. Merge thresholds directly affect final clusters.

4. Per-cluster FASTQ output materialization.
   - Primary files: `src/write_output.rs`.
   - Why it matters: the current output path clones cluster and ID maps, builds
     a read-to-cluster map, rereads sorted FASTQ, and stores cluster records
     before writing per-cluster FASTQ files.
   - Measurement: run `scripts/run-local-profiling.sh --include-fastq-output`
     and compare memory against the default `--no-fastq` handoff.
   - Output risk: low for `newONform` handoff when `final_clusters.tsv` is
     unchanged, medium for users relying on cluster FASTQ files.

5. GFF-assisted clustering path.
   - Primary files: `src/gff_handling.rs`, `src/clustering.rs`.
   - Why it matters: this path constructs initial cluster maps from annotation
     records and has different seed-generation locality than the default path.
   - Measurement: blocked until a small committed GFF fixture or external
     profiling input is approved.
   - Output risk: medium. This is an optional path, but it shares clustering
     internals with the default mode.

## Optimization Rules

- Preserve `clustering/final_clusters.tsv` compatibility for every change.
- Commit before/after local profiling reports outside Git, and cite their paths
  in review notes or release evidence.
- Run `scripts/check-output-contract-fixtures.sh` after every hot-path change.
- Run Docker toy smoke before accepting any algorithmic optimization as
  candidate release work.
- Do not mark GB10 blockers resolved from local profiling results.

