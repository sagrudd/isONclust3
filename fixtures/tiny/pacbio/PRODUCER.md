# Tiny PacBio Contract Fixture

Generated with:

```sh
cargo run --quiet -- \
  --fastq fixtures/tiny/pacbio/reads.fastq \
  --mode pacbio \
  --outfolder /tmp/isonclust3-pacbio-contract \
  --seeding minimizer \
  --no-fastq
```

Expected contract output:

```text
fixtures/tiny/pacbio/expected/final_clusters.tsv
```

GFF-assisted output generated with:

```sh
cargo run --quiet -- \
  --fastq fixtures/tiny/pacbio/reads.fastq \
  --mode pacbio \
  --outfolder /tmp/isonclust3-pacbio-gff-contract \
  --seeding minimizer \
  --no-fastq \
  --init-cl fixtures/tiny/pacbio/reference.fasta \
  --gff fixtures/tiny/pacbio/annotation.gff3
```

GFF expected contract output:

```text
fixtures/tiny/pacbio/expected/gff_final_clusters.tsv
```

The SHA-256 checksums in `checksums.sha256` cover the input FASTQ, reference
FASTA, GFF3 annotation, and expected `final_clusters.tsv` outputs. The FASTQ
fixture is intentionally strict-valid: every sequence and quality string has
identical length so downstream consumers can parse the original datatype
without repair.
