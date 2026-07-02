# isONclust3 Milestones

This roadmap brings the `sagrudd/isONclust3` fork to the same operational
maturity expected by `newONform`, `rustedBloom`, and Platage.

## Milestone 0: Fork Baseline And Governance

Goal: make the fork explicit, reproducible, and safe to integrate.

Acceptance criteria:

- `AGENTS.md`, `MILESTONES.md`, and `TODO.md` define scope and release rules.
- The repository metadata points at the maintained fork.
- Local `cargo test` passes on the upstream code.
- Known lint and modularity debt is tracked without claiming release readiness.

Status: active. The fork exists under `sagrudd/isONclust3`; `cargo test`,
`cargo fmt --check`, and `cargo clippy --all-targets -- -D warnings` pass.
Repository metadata points at the maintained fork. `RELEASE_CHECKLIST.md`,
`BLOCKERS.md`, `BENCHMARK_ACCEPTANCE.md`, CI, and `scripts/release-preflight.py`
now define the release gate. Remaining release-readiness work is centered on
Dockerized GB10 benchmark evidence and downstream generated-input checksums.

## Milestone 1: Output Contract Stabilization

Goal: make `final_clusters.tsv` a versioned, tested contract for `newONform`.

Acceptance criteria:

- The cluster table column order, identifier handling, singleton handling, and
  deterministic ordering are documented.
- Tiny fixtures cover ONT and PacBio mode outputs.
- `newONform` can consume committed `isONclust3` fixture output without adapter
  ambiguity.

Status: active. `OUTPUT_CONTRACTS.md` now defines the
`<outfolder>/clustering/final_clusters.tsv` path, two-column tab-separated
shape, no-header behavior, read-accession semantics, downstream consumer
expectations, and the current row-ordering limitation. Tiny ONT/PacBio
checksum fixtures now regenerate and exact-compare expected
`final_clusters.tsv` outputs through `scripts/check-output-contract-fixtures.sh`.
`newONform` now has downstream consumer fixtures that use committed
`isONclust3` tiny ONT and PacBio output without manual transformation.

## Milestone 2: Code Hygiene And Modularity

Goal: retire warning debt and prepare focused optimization work.

Acceptance criteria:

- `cargo clippy --all-targets -- -D warnings` passes.
- Unused imports, dead code, naming drift, and avoidable mutable state are
  removed or explicitly justified.
- Large algorithmic modules are split only where the split clarifies ownership.
- `src/main.rs` remains below 1000 lines and moves toward orchestration-only
  responsibilities.

Status: complete for the current binary crate surface. Strict clippy now passes
for all targets; fixture-backed output-contract work remains tracked under
Milestone 1.
The first hygiene pass removed unused imports, redundant struct fields,
avoidable mutable bindings, late initialization, manual prefix stripping, and
several iterator warnings, reducing strict clippy from 95 inherited errors to
43 remaining errors. The naming-normalization pass then converted internal
types, enum variants, helper names, and the parallelization module to idiomatic
Rust naming without changing the output contract, reducing strict clippy to 33
remaining errors. The first dead-code pass removed isolated legacy helpers from
the active CLI, clustering, FASTQ sorting, and seed-filtering code, reducing
strict clippy to 20 remaining errors. The remaining work is fixture-backed
GFF/FASTA dead-code triage, compatibility struct decisions, and typed
configuration structs for high-argument APIs. The configuration pass replaced
positional FASTQ sorting and GFF clustering arguments with typed module-local
configuration structs, reducing strict clippy to 17 remaining errors, all of
which were dead-code or compatibility-struct decisions. The final hygiene pass
removed the superseded GFF/FASTA resolver path, obsolete compatibility structs,
unused FASTQ scoring fields, and orphaned legacy minimizer helpers; `cargo
clippy --all-targets -- -D warnings` now passes.

## Milestone 3: Performance Profiling

Goal: identify the highest-impact optimization facets before changing
algorithms.

Acceptance criteria:

- Seed generation, minimizer/syncmer indexing, cluster assignment, GFF-assisted
  paths, and FASTQ-per-cluster output are profiled separately.
- Benchmarks report wall time, peak RSS, input size, read count, mode, k/w
  parameters, and thread count.
- Bottlenecks are ranked before implementation begins.

Status: active. `Dockerfile`, toy ONT/PacBio manifests, pending medium and
Phanerognostikon workload manifests, and `scripts/run-gb10-benchmark.sh` now
define the reproducible Docker/GB10 evidence path. Accepted GB10 reports and
large-workload `final_clusters.tsv` checksums are still blocked by
`ISOCLUST-BLOCK-001` and `ISOCLUST-BLOCK-002`.

## Milestone 4: Algorithmic Optimization

Goal: improve throughput and memory while preserving output contracts.

Candidate facets:

- Avoid unnecessary FASTQ record cloning during sorting and cluster-output
  generation.
- Reduce repeated minimizer and syncmer allocation in seed extraction.
- Replace late merge bookkeeping with explicit typed structures.
- Stream cluster FASTQ output without holding avoidable intermediate state.
- Make thread scheduling and shared-map mutation costs measurable.

Status: planned.

## Milestone 5: Dockerized GB10 Benchmarking

Goal: provide accepted benchmark evidence for the upstream clustering step used
by `newONform`.

Acceptance criteria:

- Dockerized ONT and PacBio benchmark commands run from a clean checkout.
- Reports include image digest, input checksums, output checksums, wall time,
  peak RSS, CPU architecture, and thread count.
- `newONform` benchmark manifests can cite accepted `isONclust3` cluster-table
  evidence.

Status: planned.

## Milestone 6: Tight newONform Integration

Goal: treat `isONclust3` and `newONform` as a coordinated transcriptome
consolidation product.

Acceptance criteria:

- `newONform` tracks this fork as a submodule.
- Shared fixtures prove `isONclust3 final_clusters.tsv` output is accepted by
  `newONform`.
- Release notes and blockers in both repositories identify the same upstream
  evidence gates.

Status: active. `newONform` tracks this fork as `external/isONclust3` and now
directly consumes the committed tiny ONT and PacBio output-contract fixtures.
The README documents the end-to-end handoff command sequence. Accepted upstream
producer evidence for larger workloads remains outstanding.
