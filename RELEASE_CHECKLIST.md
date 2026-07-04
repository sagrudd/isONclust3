# isONclust3 Release Checklist

Use this checklist before a release-candidate tag or before updating
`newONform` to cite `isONclust3` producer evidence.

## Required Local Checks

- [ ] `cargo fmt --check`
- [ ] `cargo test --quiet`
- [ ] `cargo clippy --all-targets -- -D warnings`
- [ ] `scripts/check-output-contract-fixtures.sh`
- [ ] `scripts/run-local-profiling.sh --case all --include-fastq-output --include-post-cluster --include-gff`
- [ ] `scripts/run-larger-workload-profiling.sh --manifest fixtures/manifests/medium-ont-cdna.json --fastq /home/stephen/gb10-verification-20260704/data/DRR138512/reads.fastq --expected-final-clusters /home/stephen/gb10-verification-20260704/data/newonform-medium-drr138512/final_clusters.tsv --output-dir target/larger-profile/drr138512 --variant default-no-fastq`
- [ ] `scripts/stage-gff-assets.sh --reference <approved-reference.fa[.gz]> --annotation <approved-annotation.gff3[.gz]> --output-dir /home/stephen/gb10-verification-20260704/data/<approved-gff-workload>`
- [ ] `sphinx-build -W -b html docs target/sphinx-html`
- [ ] Confirm `OPTIMIZATION_EVIDENCE.md` cites before/after local profiling
      for optimization commits without committing raw reports.
- [ ] `scripts/release-preflight.py --expected-version 0.3.0`
- [ ] Confirm release preflight covers the GB10 runner checksum-handoff report
      fields.
- [ ] Confirm release preflight covers the local profiling report contract as
      non-release evidence.
- [ ] `scripts/check-docker-toy-benchmarks.sh`
- [ ] `git diff --check`

## Required Docker And GB10 Evidence

- [ ] Build the benchmark image from a clean checkout.
- [ ] Run toy ONT and toy PacBio manifests through
      `scripts/check-docker-toy-benchmarks.sh`.
- [ ] Confirm accepted medium ONT manifest evidence remains archived outside Git.
- [ ] Stage the DRR178488 Phanerognostikon FASTQ with
      `scripts/stage-ena-fastq.sh`, verify the ENA MD5, and retain
      `staging-checksums.json` outside Git.
- [ ] Stage approved GFF-assisted reference FASTA and GFF3 assets with
      `scripts/stage-gff-assets.sh` and retain `gff-asset-checksums.json`
      outside Git before accepted larger-workload GFF profiling.
- [ ] Run accepted Phanerognostikon-scale ONT manifest on GB10.
- [ ] Capture JSON and TSV reports with image identity, command, input checksums,
      output checksums, wall time, peak RSS, CPU architecture, and thread count.
- [ ] Store bulky reports and generated outputs outside Git.
- [ ] Keep `ISOCLUST-BLOCK-003` active until larger-workload profiling
      evidence is recorded or explicitly waived without claiming accepted producer
      evidence.
- [ ] Confirm resolved `ISOCLUST-BLOCK-001` and `ISOCLUST-BLOCK-002` evidence
      remains visible before citing accepted GB10 producer reports or generated
      `final_clusters.tsv` checksums downstream.

## Required Integration Evidence

- [ ] Confirm `OUTPUT_CONTRACTS.md` still matches emitted
      `clustering/final_clusters.tsv`.
- [ ] Confirm the accepted medium DRR138512 `final_clusters.tsv` checksum for
      the `newONform` generated benchmark input.
- [ ] Publish accepted `final_clusters.tsv` checksums for remaining generated
      `newONform` benchmark inputs.
- [ ] Update `newONform` submodule, generated-input registers, release notes,
      blockers, and Sphinx documentation in the same release train.
- [ ] Confirm unresolved gates remain listed in `BLOCKERS.md`.
