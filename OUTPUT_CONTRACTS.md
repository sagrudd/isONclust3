# isONclust3 Output Contracts

This document defines the output contract consumed by `newONform`. It is a
release gate for the maintained `sagrudd/isONclust3` fork and must be updated
whenever output behavior changes.

## `final_clusters.tsv`

Path:

```text
<outfolder>/clustering/final_clusters.tsv
```

Format:

- UTF-8 text.
- No header row.
- One read assignment per line.
- Exactly two tab-separated columns per line.
- Column 1: decimal integer cluster ID emitted by `isONclust3`.
- Column 2: read accession emitted from the FASTQ record identifier, without
  the leading `@`.
- Line ending: `\n`.

Example:

```text
0	read_X_acc
0	read_Y_acc
1	read_Z_acc
```

Semantics:

- Every row assigns one accepted read to one cluster.
- Singleton clusters are valid.
- Cluster IDs are process-local identifiers, not biological labels.
- Read accessions must match the corresponding FASTQ identifiers consumed by
  downstream tools.
- Consumers, including `newONform`, must group rows by cluster ID and must not
  infer biological ordering from row order.

Compatibility notes:

- The two-column tab-separated shape is stable for `newONform`.
- Row ordering is exact-regression checked for the committed tiny ONT and
  PacBio fixtures. GB10 release evidence must still record generated output
  checksums for larger workloads.
- Resolved tiny fixture output and paired FASTQ checksums are recorded in
  `fixtures/output-contracts/final-clusters-register.json` for downstream
  `newONform` producer evidence. The register must point at and conform to
  `schemas/output-contract-register.schema.json`.
- Regenerate and verify committed tiny fixtures with:

  ```sh
  scripts/check-output-contract-fixtures.sh
  ```

- Any change to path, column count, delimiter, header behavior, cluster ID
  encoding, or read accession encoding is an output-contract change and must
  update `newONform` fixtures and documentation in the same release train.

## Cluster FASTQ Files

When `--no-fastq` is not set, per-cluster FASTQ files are written under:

```text
<outfolder>/clustering/fastq_files/
```

These files are useful for inspection and legacy behavior compatibility, but
`newONform` treats `final_clusters.tsv` plus the original FASTQ input as the
stable integration interface.
