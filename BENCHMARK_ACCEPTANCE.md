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

## Initial Gates

- Toy ONT and toy PacBio fixtures must pass checksum-backed regeneration.
- Before GB10 execution, toy ONT and toy PacBio manifests must pass the local
  Docker smoke in `scripts/check-docker-toy-benchmarks.sh`; this confirms the
  benchmark image, runner report path, and `final_clusters.tsv` checksums.
- Benchmark manifests must keep the file-based handoff command shape:
  `--fastq`, `--mode`, `--outfolder`, `--seeding`, and `--no-fastq` under the
  `isonclust3:gb10` image, with `--mode` and `--seeding` matching the manifest
  metadata.
- Medium ONT and Phanerognostikon-scale workloads must not be accepted until
  their source inputs, producer commands, and generated cluster-table checksums
  are recorded.
- Medium ONT and Phanerognostikon-scale manifests must record the downstream
  `newONform` generated-input register entry they unblock under `NOF-BLOCK-006`.
- Any algorithmic optimization must include before/after reports for at least
  one toy fixture and the smallest relevant larger workload.
- Bulky raw data, generated output directories, and GB10 reports must remain
  outside Git unless explicitly whitelisted as tiny fixtures.
