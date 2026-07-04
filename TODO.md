# isONclust3 TODO

Tasks are ordered to improve the fork without breaking the upstream
`final_clusters.tsv` contract consumed by `newONform`.

## 1. Governance And Release Discipline

- [x] Confirm the maintained fork exists under `sagrudd/isONclust3`.
- [x] Add `AGENTS.md`, `MILESTONES.md`, and `TODO.md`.
- [x] Update package metadata for the maintained fork while preserving upstream
      attribution.
- [x] Add a release checklist and blocker register.
- [x] Add release notes for the first maintained fork release-candidate cycle.
- [x] Gate release-checklist sections and unchecked operator-template status in
      release preflight.
- [x] Gate active and resolved blocker-register rows in release preflight.
- [x] Add preflight checks for version syntax, file-size limits, fixture
      hygiene, and documentation markers.
- [x] Gate GB10 milestone active status and unresolved evidence blockers.
- [x] Gate release-checklist visibility for active benchmark blocker IDs.
- [x] Gate TODO visibility for unresolved evidence tasks.
- [x] Gate release-note scope, evidence, known-limit, and no-tag markers.
- [x] Add Sphinx governance and release-readiness source pages.
- [x] Add Sphinx warning-as-error build to CI and release checklist.
- [x] Gate README release-readiness documentation build instructions.
- [x] Gate Sphinx release-readiness documentation build instructions.
- [x] Gate AGENTS Sphinx documentation policy markers.
- [x] Gate release-checklist downstream handoff artifact markers.
- [x] Gate blocker waiver rules for upstream producer evidence.
- [x] Gate Sphinx waiver-boundary release-readiness markers.
- [x] Gate Sphinx index waiver-scope status markers.
- [x] Gate README waiver-scope release evidence markers.
- [x] Gate release-note waiver-scope operator markers.
- [x] Gate benchmark acceptance waiver-scope status markers.
- [x] Gate Sphinx index generated-checksum waiver-scope markers.
- [x] Gate release-checklist waiver-scope evidence markers.
- [x] Gate AGENTS compatibility-waiver evidence markers.
- [x] Gate expanded tracked-artifact hygiene markers.
- [x] Gate .gitignore generated-artifact markers.
- [x] Split tracked-artifact hygiene into a focused preflight module.
- [x] Gate a machine-readable tiny `final_clusters.tsv` output-contract
      register.
- [x] Gate paired FASTQ checksums in the tiny output-contract register.
- [x] Gate the output-contract register schema.
- [x] Gate output-contract schema entry constraints.
- [x] Gate output-contract register paths as relative and non-escaping.
- [x] Gate output-contract schema path patterns.
- [x] Gate output-contract register entry ordering.
- [x] Gate output-contract schema entry count.
- [x] Gate output-contract schema exact entry count.
- [x] Gate output-contract schema scalar entry constraints.
- [x] Gate output-contract schema property types.
- [x] Gate output-contract schema required field ordering.
- [x] Gate output-contract schema property ordering.
- [x] Gate output-contract schema catalog title.
- [x] Gate output-contract schema entry ID enum.
- [x] Gate output-contract schema unique entry rows.
- [x] Gate output-contract schema definition keys.
- [x] Gate output-contract schema root property types.
- [x] Gate output-contract schema readability and object root.
- [x] Gate output-contract register root key ordering.
- [x] Gate output-contract register entry key ordering.
- [x] Gate output-contract register readability and object root.

## 2. Output Contract Harmonization

- [x] Document `final_clusters.tsv` as the stable `newONform` input contract.
- [x] Add tiny ONT fixture output with checksum-backed `final_clusters.tsv`.
- [x] Add tiny PacBio fixture output with checksum-backed `final_clusters.tsv`.
- [x] Add deterministic ordering checks for cluster table output.
- [x] Add a consumer fixture in `newONform` that reads committed `isONclust3`
      output without manual transformation.

## 3. Strict Lint And Hygiene

- [x] Apply repository-wide `cargo fmt` normalization.
- [x] Make `cargo clippy --all-targets -- -D warnings` pass.
  - [x] Remove unused imports.
  - [x] Remove or justify dead code.
    - [x] Remove isolated legacy helpers from `main.rs`, clustering, and
          seed-filtering code that were not reachable from the active CLI.
    - [x] Remove dormant GFF/FASTA helpers that were superseded by the active
          `gff_based_clustering` path.
    - [x] Decide whether unused compatibility structs should become fixture
          API types or be removed.
  - [x] Rename non-camel-case types and variants without changing output.
  - [x] Remove avoidable mutable bindings and late initialization.
  - [x] Replace redundant struct field initializers.
  - [x] Triage high-argument functions into typed configuration structs.
- [x] Add `cargo fmt --check`, `cargo test`, and clippy to CI.

## 4. Performance Deep Dive

- [x] Add a local profiling harness for toy ONT/PacBio runs that records
      wall time, peak RSS, checksums, and output-contract status.
- [x] Add a larger-workload profiling harness for accepted external manifests
      that records wall time, peak RSS, checksums, and output-contract status
      without committing raw reports.
- [x] Gate the local profiling harness report contract as non-release evidence.
- [x] Rank optimization candidates by wall-time, memory, and output-risk.
- [x] Gate larger-workload manifests with seed-generation and minimizer
      extraction profiling plans before acceptance.
- [x] Profile seed generation and minimizer/syncmer extraction on the smallest
      accepted larger workload.
- [x] Profile clustering merge bookkeeping and shared-seed maps with
      post-clustering enabled.
- [x] Profile FASTQ record sorting and per-cluster output generation with
      `--include-fastq-output` and accepted medium DRR138512 write-FASTQ
      larger-workload evidence.
- [x] Profile GFF-assisted clustering separately from the default path.

## 5. Optimizations

- [x] Reduce unnecessary FASTQ record cloning.
  - [x] Avoid cloning the full cluster and read-ID maps while writing
        `final_clusters.tsv`.
  - [x] Stream parsed FASTQ records into the per-cluster output map without an
        intermediate all-record vector.
- [x] Reduce repeated minimizer/syncmer allocation.
  - [x] Make seed records copyable and avoid cloning filtered minimizer records.
  - [x] Avoid copying the PHRED lookup table and unused quality-probability
        vector during seed-quality filtering.
  - [x] Use fixed PHRED count storage during FASTQ sorting quality scoring.
- [x] Replace ad hoc tuple merge bookkeeping with named structs.
- [x] Stream cluster FASTQ output where possible.
- [ ] Add benchmark evidence before and after every algorithmic optimization.
  - [x] Add a preflight-validated optimization evidence ledger for local
        before/after profiling notes.
  - [x] Gate optimization evidence entry fields and contract-check markers in
        release preflight.
  - [x] Gate optimization evidence profiling commands and ignored report paths.
  - [x] Gate optimization evidence commit SHAs against repository history.
  - [x] Gate optimization evidence commits as reachable from release HEAD.

## 6. Dockerized GB10 Evidence

- [x] Add a Dockerfile for release and benchmark execution.
- [x] Add benchmark manifests for toy ONT, toy PacBio, medium ONT, and
      Phanerognostikon-scale ONT workloads.
  - [x] Gate downstream `newONform` generated-input handoff IDs for pending
        medium and Phanerognostikon-scale producer manifests.
  - [x] Gate pending external workload manifests against `ISOCLUST-BLOCK-002`
        until accepted input and output checksums exist.
  - [x] Gate benchmark manifest command shape for the file-based
        `final_clusters.tsv` handoff.
  - [x] Gate benchmark manifest command flags against the supported flag set.
  - [x] Gate benchmark manifest command flags so each appears exactly once.
  - [x] Gate benchmark manifest command argument order.
  - [x] Gate benchmark manifest command values against mode, seeding, and
        container path metadata.
  - [x] Gate benchmark manifests so every evidence run requires a container
        digest.
  - [x] Gate benchmark manifests so every evidence workload targets
        `linux/arm64` for GB10 execution.
  - [x] Gate benchmark manifest platform target vocabulary.
  - [x] Gate benchmark manifest source provenance and toy fixture license.
  - [x] Gate benchmark manifest acceptance object structure.
  - [x] Gate benchmark acceptance classes and report-field markers.
  - [x] Gate benchmark manifest kind and seeding metadata.
  - [x] Gate benchmark manifest schema version and tier vocabulary.
  - [x] Gate benchmark manifest schema path markers.
  - [x] Gate benchmark manifest schema contract markers.
  - [x] Gate benchmark manifest schema structural constraints.
  - [x] Gate benchmark manifest schema root key ordering.
  - [x] Gate benchmark manifest schema nested type policy.
  - [x] Gate benchmark manifest schema non-empty string policy.
  - [x] Gate benchmark manifest schema property ordering.
  - [x] Gate benchmark manifest schema additionalProperties policy.
  - [x] Gate benchmark manifest schema nested required field ordering.
  - [x] Gate benchmark manifest keys against the benchmark schema.
  - [x] Gate benchmark manifest checksum keys against the benchmark schema.
  - [x] Gate benchmark manifest key ordering against the benchmark schema.
  - [x] Gate benchmark manifest filename-to-ID identity and uniqueness.
  - [x] Gate benchmark manifest readability and object root.
  - [x] Gate toy benchmark manifest file-role coverage.
  - [x] Gate toy benchmark manifest file-role paths.
  - [x] Gate benchmark manifest duplicate file roles.
  - [x] Gate benchmark manifest duplicate file paths.
  - [x] Gate benchmark manifest file-entry structure.
  - [x] Gate benchmark manifest file checksum value shape.
- [x] Add a GB10 runner that records command, image, checksums, wall time,
      peak RSS, CPU architecture, and thread count.
- [x] Gate GB10 runner report fields for generated `final_clusters.tsv`
      checksum handoff.
- [x] Add an ENA FASTQ staging helper for Phanerognostikon DRR178488 GB10
      producer evidence.
- [x] Add a local Docker toy benchmark smoke for ONT and PacBio manifests.
- [x] Record accepted GB10 benchmark reports with command, image, checksums,
      wall time, peak RSS, CPU architecture, and thread count.
  - [x] Record accepted toy ONT and toy PacBio GB10 reports with source commit,
        tool version, image digest, checksums, wall time, peak RSS, CPU
        architecture, and thread count.
  - [x] Record accepted medium ONT GB10 reports after generated input and
        output checksums are available.
  - [x] Record accepted Phanerognostikon DRR178488 ONT GB10 reports after
        generated input and output checksums are available.
  - [x] Record accepted Phanerognostikon-scale ONT GB10 reports after generated
        input and output checksums are available.
- [x] Expose generated `final_clusters.tsv` checksums for `newONform` release
      evidence.

## 7. newONform Product Integration

- [x] Track `sagrudd/isONclust3` as a `newONform` submodule.
- [x] Document the end-to-end `isONclust3 -> newONform` transcriptome
      consolidation workflow.
- [x] Add a shared fixture path that lets `newONform` validate `isONclust3`
      output directly.
- [x] Keep `newONform` generated-input registers aligned with accepted
      `isONclust3` output checksums.
