# isONclust3 TODO

Tasks are ordered to improve the fork without breaking the upstream
`final_clusters.tsv` contract consumed by `newONform`.

## 1. Governance And Release Discipline

- [x] Confirm the maintained fork exists under `sagrudd/isONclust3`.
- [x] Add `AGENTS.md`, `MILESTONES.md`, and `TODO.md`.
- [x] Update package metadata for the maintained fork while preserving upstream
      attribution.
- [ ] Add a release checklist and blocker register.
- [ ] Add preflight checks for version syntax, file-size limits, fixture
      hygiene, and documentation markers.

## 2. Output Contract Harmonization

- [ ] Document `final_clusters.tsv` as the stable `newONform` input contract.
- [ ] Add tiny ONT fixture output with checksum-backed `final_clusters.tsv`.
- [ ] Add tiny PacBio fixture output with checksum-backed `final_clusters.tsv`.
- [ ] Add deterministic ordering checks for cluster table output.
- [ ] Add a consumer fixture in `newONform` that reads committed `isONclust3`
      output without manual transformation.

## 3. Strict Lint And Hygiene

- [x] Apply repository-wide `cargo fmt` normalization.
- [ ] Make `cargo clippy --all-targets -- -D warnings` pass.
  - [x] Remove unused imports.
  - [ ] Remove or justify dead code.
    - [x] Remove isolated legacy helpers from `main.rs`, clustering, and
          seed-filtering code that were not reachable from the active CLI.
    - [ ] Preserve or fixture-test dormant GFF/FASTA helpers before removal.
    - [ ] Decide whether unused compatibility structs should become fixture
          API types or be removed.
  - [x] Rename non-camel-case types and variants without changing output.
  - [x] Remove avoidable mutable bindings and late initialization.
  - [x] Replace redundant struct field initializers.
  - [ ] Triage high-argument functions into typed configuration structs.
- [ ] Add `cargo fmt --check`, `cargo test`, and clippy to CI.

## 4. Performance Deep Dive

- [ ] Profile seed generation and minimizer/syncmer extraction.
- [ ] Profile clustering merge bookkeeping and shared-seed maps.
- [ ] Profile FASTQ record sorting and per-cluster output generation.
- [ ] Profile GFF-assisted clustering separately from the default path.
- [ ] Rank optimization candidates by wall-time, memory, and output-risk.

## 5. Optimizations

- [ ] Reduce unnecessary FASTQ record cloning.
- [ ] Reduce repeated minimizer/syncmer allocation.
- [ ] Replace ad hoc tuple merge bookkeeping with named structs.
- [ ] Stream cluster FASTQ output where possible.
- [ ] Add benchmark evidence before and after every algorithmic optimization.

## 6. Dockerized GB10 Evidence

- [ ] Add a Dockerfile for release and benchmark execution.
- [ ] Add benchmark manifests for toy ONT, toy PacBio, medium ONT, and
      Phanerognostikon-scale ONT workloads.
- [ ] Record GB10 benchmark reports with command, image, checksums, wall time,
      peak RSS, CPU architecture, and thread count.
- [ ] Expose generated `final_clusters.tsv` checksums for `newONform` release
      evidence.

## 7. newONform Product Integration

- [x] Track `sagrudd/isONclust3` as a `newONform` submodule.
- [ ] Document the end-to-end `isONclust3 -> newONform` transcriptome
      consolidation workflow.
- [ ] Add a shared fixture path that lets `newONform` validate `isONclust3`
      output directly.
- [ ] Keep `newONform` generated-input registers aligned with accepted
      `isONclust3` output checksums.
