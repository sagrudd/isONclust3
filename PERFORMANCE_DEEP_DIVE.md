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
must not be committed. Summarize accepted local before/after optimization
evidence in `OPTIMIZATION_EVIDENCE.md` instead of committing raw reports.

Use `--include-fastq-output` when profiling per-cluster FASTQ materialization,
`--include-post-cluster` when profiling merge refinement behavior, and
`--include-gff` when profiling annotation-seeded initialization. These variants
are intentionally opt-in because they measure different code paths than the
default `newONform` handoff, which uses `--no-fastq`.

## Ranked Facets

1. Seed extraction and filtering in the sorting pass.
   - Primary files: `src/generate_sorted_fastq_for_cluster.rs`,
     `src/seeding_and_filtering_seeds.rs`.
   - Why it matters: each read builds a fresh `Vec<MinimizerHashed>` and then
     filters it before sorting reads by high-confidence seed count.
   - Measurement: compare ONT and PacBio local profiling reports with default
     `--no-fastq`, then repeat on the smallest accepted larger workload before
     changing allocation behavior.
     Medium and Phanerognostikon manifests must keep a preflight-validated
     `profiling_plan` that covers seed generation, minimizer extraction,
     quality filtering, and exact `final_clusters.tsv` compatibility before
     those workloads can become accepted evidence.
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
   - Why it matters: the output path builds a read-to-cluster map and rereads
     sorted FASTQ; the current implementation streams eligible cluster records
     directly to per-cluster writers instead of storing a full
     cluster-to-record map first.
   - Measurement: run `scripts/run-local-profiling.sh --include-fastq-output`
     and compare memory against the default `--no-fastq` handoff.
   - Output risk: low for `newONform` handoff when `final_clusters.tsv` is
     unchanged, medium for users relying on cluster FASTQ files.

5. GFF-assisted clustering path.
   - Primary files: `src/gff_handling.rs`, `src/clustering.rs`.
   - Why it matters: this path constructs initial cluster maps from annotation
     records and has different seed-generation locality than the default path.
   - Measurement: run `scripts/run-local-profiling.sh --include-gff` against
     the committed tiny ONT/PacBio reference FASTA and GFF3 fixtures, then
     repeat with an approved external profiling input before making
     release-evidence claims.
   - Output risk: medium. This is an optional path, but it shares clustering
     internals with the default mode.

## Optimization Rules

- Preserve `clustering/final_clusters.tsv` compatibility for every change.
- Keep before/after local profiling reports outside Git, and cite their paths
  in `OPTIMIZATION_EVIDENCE.md`, review notes, or release evidence.
- Run `scripts/check-output-contract-fixtures.sh` after every hot-path change.
- Run Docker toy smoke before accepting any algorithmic optimization as
  candidate release work.
- Do not mark GB10 blockers resolved from local profiling results.
