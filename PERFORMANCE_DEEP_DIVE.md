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

Run accepted larger-workload profiling with:

```sh
scripts/run-larger-workload-profiling.sh \
  --manifest fixtures/manifests/medium-ont-cdna.json \
  --fastq /home/stephen/gb10-verification-20260704/data/DRR138512/reads.fastq \
  --expected-final-clusters /home/stephen/gb10-verification-20260704/data/newonform-medium-drr138512/final_clusters.tsv \
  --output-dir target/larger-profile/drr138512 \
  --variant default-no-fastq
```

The larger-workload-profiling harness records the accepted manifest metadata,
profiling plan, wall time, peak RSS, input checksum, generated
`final_clusters.tsv` checksum, and exact contract status. Reports are still
non-release evidence and must remain under ignored `target/` paths unless
release owners explicitly move summaries into a reviewed evidence register.

Accepted larger-workload default-path profiling is archived outside Git under:

```text
/home/stephen/gb10-verification-20260704/results/isONclust3-larger-profile-drr138512-7a3f390/reports/drr138512-default-no-fastq-7a3f390.json
```

The DRR138512 run completed on GB10 Linux ARM64 with exit code 0, 161.454274
seconds wall time, 2161.68 MiB peak RSS, input FASTQ checksum
`1280e7af119051204874163263b59abbbcf9a9f1a4a9384674b240959029bf03`,
generated `final_clusters.tsv` checksum
`a37798b916ba5078ca90bed40946ad694bbae957d724034a51e040689406acc7`, and exact
contract match against the accepted expected checksum. This covers
seed-generation, minimizer-extraction, quality-filtering, final-clusters
contract, handoff-no-fastq, and default-clustering facets for the smallest
accepted larger workload.

Accepted larger-workload cluster FASTQ output profiling is archived outside Git
under:

```text
/home/stephen/gb10-verification-20260704/results/isONclust3-larger-profile-drr138512-313a7f7-write-fastq/reports/drr138512-write-fastq-313a7f7.json
```

The write-FASTQ DRR138512 run completed on GB10 Linux ARM64 with exit code 0,
186.226314 seconds wall time, 2162.18 MiB peak RSS, the same input FASTQ
checksum, generated `final_clusters.tsv` checksum
`a37798b916ba5078ca90bed40946ad694bbae957d724034a51e040689406acc7`, and exact
contract match. This covers seed-generation, minimizer-extraction,
quality-filtering, final-clusters contract, fastq-output, and
default-clustering facets for the smallest accepted larger workload.

Rejected larger-workload post-cluster profiling is archived outside Git under:

```text
/home/stephen/gb10-verification-20260704/results/isONclust3-larger-profile-drr138512-7c29eec-post-cluster/reports/drr138512-post-cluster-7c29eec.json
```

The post-cluster DRR138512 run completed with process exit code 0, 438.801846
seconds wall time, and 2161.395 MiB peak RSS, but it changed
`final_clusters.tsv` from the accepted checksum
`a37798b916ba5078ca90bed40946ad694bbae957d724034a51e040689406acc7` to
`cab07475f8e3559187191f86f50a5c7534658ad960cb881dd837b5305f3ad547`.
Treat this as rejected handoff evidence for the accepted medium workload until
release owners either define a separate post-cluster compatibility class or
approve a scoped waiver.

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
     Medium DRR138512 default-path evidence is recorded under
     `/home/stephen/gb10-verification-20260704/results/isONclust3-larger-profile-drr138512-7a3f390/`.
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
     Medium DRR138512 post-cluster evidence is rejected for handoff
     compatibility because the generated `final_clusters.tsv` checksum differs
     from the accepted default-path checksum.
   - Output risk: high. Merge thresholds directly affect final clusters.

4. Per-cluster FASTQ output materialization.
   - Primary files: `src/write_output.rs`.
   - Why it matters: the output path builds a read-to-cluster map and rereads
     sorted FASTQ; the current implementation streams eligible cluster records
     directly to per-cluster writers instead of storing a full
     cluster-to-record map first.
   - Measurement: run `scripts/run-local-profiling.sh --include-fastq-output`
     and compare memory against the default `--no-fastq` handoff.
     Medium DRR138512 write-FASTQ evidence is recorded under
     `/home/stephen/gb10-verification-20260704/results/isONclust3-larger-profile-drr138512-313a7f7-write-fastq/`.
   - Output risk: low for `newONform` handoff when `final_clusters.tsv` is
     unchanged, medium for users relying on cluster FASTQ files.

5. GFF-assisted clustering path.
   - Primary files: `src/gff_handling.rs`, `src/clustering.rs`.
   - Why it matters: this path constructs initial cluster maps from annotation
     records and has different seed-generation locality than the default path.
   - Measurement: run `scripts/run-local-profiling.sh --include-gff` against
     the committed tiny ONT/PacBio reference FASTA and GFF3 fixtures, then
     repeat with `scripts/run-larger-workload-profiling.sh --variant
     gff-assisted --reference-fasta <reference.fa> --annotation-gff
     <annotation.gff3>` against an approved external profiling input before
     making release-evidence claims.
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
