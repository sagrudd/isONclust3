# isONclust3 Benchmark Acceptance Criteria

`isONclust3` benchmark acceptance prioritizes output-contract compatibility
before speed. A run is not release evidence unless it preserves
`clustering/final_clusters.tsv` semantics and records enough provenance for
`newONform` to consume the cluster table.

## Required Report Fields

Every accepted Dockerized or GB10 report must include:

- `isONclust3` version and Git commit.
- Container image ID or digest.
- Host operating system, CPU architecture, platform target, and thread count.
- Manifest ID, benchmark tier, mode, seeding mode, and dataset description.
- Input FASTQ checksum and generated `final_clusters.tsv` checksum.
- Full command line.
- Exit code, wall time, peak RSS status, and peak RSS when measurable.
- Output paths for the JSON report, TSV summary, run log, and Docker stats log.

## Acceptance Classes

- `accepted_contract`: the run exits successfully and emits a checksum-backed
  `final_clusters.tsv` matching the documented two-column contract.
- `accepted_calibration`: the run exits successfully and records time/memory,
  but no release threshold exists yet for the tier.
- `rejected_contract`: the cluster table is missing or violates the contract.
- `rejected_operational`: Docker, command, checksum, or report provenance is
  incomplete.
- `blocked_pending_data`: the source data or generated cluster table is not yet
  available for release evidence.
- Waived producer gaps remain scoped release limitations and must not be
  reported as `accepted_contract` or `accepted_calibration` benchmark evidence.

## Initial Gates

- Toy ONT and toy PacBio fixtures must pass checksum-backed regeneration.
- Every benchmark manifest must include `linux/arm64` in `platform_targets` so
  Dockerized GB10 execution remains an explicit release requirement.
- Benchmark `platform_targets` must use the supported Linux target vocabulary:
  `linux/arm64` for GB10 and `linux/amd64` for local toy smoke where needed.
- Benchmark manifests must identify themselves as
  `isonclust3-benchmark-fixture` and record the seeding mode used by the
  command.
- Benchmark manifests must use schema version 1 and one of the accepted
  benchmark tiers: `toy`, `medium`, or `phanerognostikon`.
- Benchmark manifests must keep filename-derived IDs, remain unique, and stay
  inside the release-known manifest set.
- Benchmark manifests must include populated source descriptions; committed toy
  sources must record the `GPL-3.0-only` fixture license.
- Benchmark manifest `acceptance` entries must be represented as objects before
  GB10 report, container digest, and checksum gates are evaluated.
- Toy benchmark manifests must include checksum-backed `input-fastq` and
  `expected-final-clusters` file roles pointing at the canonical toy
  `reads.fastq` and `expected/final_clusters.tsv` paths.
- Benchmark manifest `files` entries must be represented as a list of objects.
- Manifest file checksums must use lowercase 64-character SHA-256 hex values.
- Before GB10 execution, toy ONT and toy PacBio manifests must pass the local
  Docker smoke in `scripts/check-docker-toy-benchmarks.sh`; this confirms the
  benchmark image, runner report path, and `final_clusters.tsv` checksums.
- Benchmark manifests must keep the file-based handoff command shape:
  `--fastq`, `--mode`, `--outfolder`, `--seeding`, and `--no-fastq` under the
  `isonclust3:gb10` image, with `--mode` and `--seeding` matching the manifest
  metadata, no unrecognized command flags, and each supported flag appearing
  exactly once in the canonical file-based handoff sequence.
- Medium ONT and Phanerognostikon-scale workloads must not be accepted until
  their source inputs, producer commands, and generated cluster-table checksums
  are recorded.
- Waived medium or Phanerognostikon producer gaps do not claim accepted GB10
  producer evidence or generated `final_clusters.tsv` checksum readiness.
- Medium ONT and Phanerognostikon-scale manifests must record the downstream
  `newONform` generated-input register entry they unblock under `NOF-BLOCK-006`.
- Any algorithmic optimization must include before/after reports for at least
  one toy fixture and the smallest relevant larger workload.
- Bulky raw data, generated output directories, and GB10 reports must remain
  outside Git unless explicitly whitelisted as tiny fixtures.
