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

The SHA-256 checksums in `checksums.sha256` cover the input FASTQ and expected
`final_clusters.tsv`.
