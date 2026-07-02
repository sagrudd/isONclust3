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

Status: active. The fork exists under `sagrudd/isONclust3`; `cargo test`
passes, repository metadata now points at the maintained fork, and code is
normalized with `cargo fmt`. Strict clippy currently exposes warning debt that
must be retired before the fork can act as a release-quality upstream
dependency.

## Milestone 1: Output Contract Stabilization

Goal: make `final_clusters.tsv` a versioned, tested contract for `newONform`.

Acceptance criteria:

- The cluster table column order, identifier handling, singleton handling, and
  deterministic ordering are documented.
- Tiny fixtures cover ONT and PacBio mode outputs.
- `newONform` can consume committed `isONclust3` fixture output without adapter
  ambiguity.

Status: planned.

## Milestone 2: Code Hygiene And Modularity

Goal: retire warning debt and prepare focused optimization work.

Acceptance criteria:

- `cargo clippy --all-targets -- -D warnings` passes.
- Unused imports, dead code, naming drift, and avoidable mutable state are
  removed or explicitly justified.
- Large algorithmic modules are split only where the split clarifies ownership.
- `src/main.rs` remains below 1000 lines and moves toward orchestration-only
  responsibilities.

Status: active. Current strict clippy fails with unused imports, unused
variables, dead-code warnings, naming warnings, redundant struct fields, and
several mechanical cleanup opportunities.
The first hygiene pass removed unused imports, redundant struct fields,
avoidable mutable bindings, late initialization, manual prefix stripping, and
several iterator warnings, reducing strict clippy from 95 inherited errors to
43 remaining errors. The remaining work is naming normalization, dead-code
triage, and typed configuration structs for high-argument APIs.

## Milestone 3: Performance Profiling

Goal: identify the highest-impact optimization facets before changing
algorithms.

Acceptance criteria:

- Seed generation, minimizer/syncmer indexing, cluster assignment, GFF-assisted
  paths, and FASTQ-per-cluster output are profiled separately.
- Benchmarks report wall time, peak RSS, input size, read count, mode, k/w
  parameters, and thread count.
- Bottlenecks are ranked before implementation begins.

Status: planned.

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

Status: active. `newONform` tracks this fork as `external/isONclust3`; shared
fixtures and accepted upstream producer evidence remain outstanding.
