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

The SHA-256 checksums in `checksums.sha256` cover the input FASTQ and expected
`final_clusters.tsv`.
