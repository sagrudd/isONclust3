# Tiny ONT Contract Fixture

Generated with:

```sh
cargo run --quiet -- \
  --fastq fixtures/tiny/ont/reads.fastq \
  --mode ont \
  --outfolder /tmp/isonclust3-ont-contract \
  --seeding minimizer \
  --no-fastq
```

Expected contract output:

```text
fixtures/tiny/ont/expected/final_clusters.tsv
```

GFF-assisted output generated with:

```sh
cargo run --quiet -- \
  --fastq fixtures/tiny/ont/reads.fastq \
  --mode ont \
  --outfolder /tmp/isonclust3-ont-gff-contract \
  --seeding minimizer \
  --no-fastq \
  --init-cl fixtures/tiny/ont/reference.fasta \
  --gff fixtures/tiny/ont/annotation.gff3
```

GFF expected contract output:

```text
fixtures/tiny/ont/expected/gff_final_clusters.tsv
```

The SHA-256 checksums in `checksums.sha256` cover the input FASTQ, reference
FASTA, GFF3 annotation, and expected `final_clusters.tsv` outputs.
