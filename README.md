# isONclust3

isONclust3 is a tool for clustering either PacBio Iso-Seq reads, or Oxford Nanopore reads into clusters, where each cluster represents all reads that came from a gene family. Output is a tsv file with each read assigned to a cluster-ID and a folder 'fastq' containing one fastq file per cluster generated. Detailed information is available in the [isONclust3 paper](https://doi.org/10.1093/bioinformatics/btaf207).

This repository is the `sagrudd/isONclust3` maintained fork used as the
upstream clustering-stage dependency for `newONform` transcriptome
consolidation. Upstream authorship and citation remain unchanged; fork changes
focus on release hygiene, output-contract evidence, and GB10-aware benchmark
readiness.

# Table of contents
1. [Installation](#installation)
2. [Output](#output)
3. [Running isONclust3](#Running)
4. [Contact](#contact)
5. [Credits](#credits)

# Installation <a name="installation"></a>
The installation of isONclust3 requires users to install the Rust programming language onto their system.

## Installing Rust <a name="installingrust"></a>
You can install rust via<br />

`curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh` (for macOS and Linux or other Unix-based OS). For Windows please follow the instructions on the following site: https://forge.rust-lang.org/infra/other-installation-methods.html .<br />

## Installing isONclust3

You can install isONclust3 from the cargo package manager or from source.

### From Cargo package manager <a name="installation cargo"></a>
When you have installed Rust run  `cargo install isONclust3` to install the binary globally.

### From GitHub source <a name="installation source"></a>
```
git clone https://github.com/sagrudd/isONclust3.git
cd isONclust3
cargo build --release
```
The executable is then located in folder `target/release`.

### Testing the installation <a name="installation"></a>
Run `target/release/isONclust3 --fastq example_data/test_data.fastq --mode ont --outfolder example_out --seeding minimizer --post-cluster`.

This generates an output directory in the repository folder. The fastq_files folder inside clustering should now contain 94 fastq files(each representing one cluster).

# Running isONclust3 <a name="Running"></a>
IsONclust3 can be used on either Pacbio data or ONT data.

```
isONclust3 --fastq {input.fastq} --mode ont  --outfolder {outfolder}         # Oxford Nanopore reads
isONclust3 --fastq {input.fastq} --mode pacbio  --outfolder {outfolder}      # PacBio reads

```

The `--mode ont` argument means setting `--k 13 --w 21`. The `--mode pacbio` argument is equal to setting `--k 15 --w 51`.

# Output <a name="output"></a>

### Clustering information
The stable downstream integration output is
`<outfolder>/clustering/final_clusters.tsv`. The file has no header and uses
exactly two tab-separated columns: cluster ID and read accession. For example:
```
0	read_X_acc
0	read_Y_acc
...
n	read_Z_acc
```
Each row assigns one accepted read to one cluster. Some reads might be
singletons. Consumers must not rely on row ordering until the deterministic
ordering fixture gate is complete.

See [`OUTPUT_CONTRACTS.md`](OUTPUT_CONTRACTS.md) for the maintained
`final_clusters.tsv` contract consumed by `newONform`.

# End-To-End newONform Workflow

`isONclust3` is the cluster-table producer in the maintained transcriptome
consolidation workflow. The handoff to `newONform` uses the original FASTQ and
the emitted `final_clusters.tsv` without an adapter step:

```sh
isONclust3 \
  --fastq reads.fastq \
  --mode ont \
  --outfolder isonclust3_out \
  --seeding minimizer \
  --no-fastq

newONform \
  --fastq reads.fastq \
  --final-clusters isonclust3_out/clustering/final_clusters.tsv \
  --outfolder newonform_out \
  --iso_abundance 5
```

For PacBio input, switch the first command to `--mode pacbio`; the handoff path
and `newONform` command are unchanged. Tiny ONT and PacBio fixtures in
`fixtures/tiny/*` prove this interface in two directions: this repository
regenerates the committed `final_clusters.tsv` outputs, and `newONform` consumes
those committed outputs directly through its `external/isONclust3` submodule.

Release evidence for medium and Phanerognostikon-scale workloads must use the
same handoff and must publish the generated `final_clusters.tsv` checksums for
`newONform` before those runs can be accepted.

# Release And Benchmark Evidence

This maintained fork gates release-candidate evidence through:

- [`RELEASE_CHECKLIST.md`](RELEASE_CHECKLIST.md) for the local and GB10 release
  checklist.
- [`BLOCKERS.md`](BLOCKERS.md) for unresolved upstream producer-evidence gaps.
- [`BENCHMARK_ACCEPTANCE.md`](BENCHMARK_ACCEPTANCE.md) for Dockerized and GB10
  benchmark report requirements.
- `fixtures/manifests/*.json` for toy and pending larger workload manifests.

Waivers must stay visible as scoped release limitations and do not claim accepted GB10 producer evidence or generated `final_clusters.tsv` checksum readiness for `newONform`.

Run the local release preflight with:

```sh
scripts/release-preflight.py --expected-version 0.3.0
```

Build the Sphinx governance and release-readiness documentation with warnings
as errors:

```sh
python -m pip install -r docs/requirements.txt
sphinx-build -W -b html docs target/sphinx-html
```

Build the benchmark image from a clean checkout with:

```sh
docker build --platform linux/arm64 -t isonclust3:gb10 .
```

Current GB10/DGX Spark verification access is `stephen@192.168.1.48` using
the local private key at `/Users/stephen/.ssh/dgx_spark.pem`. Do not copy the
PEM into this repository or generated benchmark artifacts. The July 2026 probe
identified the host as `spark-964a`, running ARM64 Linux with Docker and
`nvidia-smi` available for GB10 evidence collection.

Then run toy or externally mounted GB10 workloads through
`scripts/run-gb10-benchmark.sh`. Generated reports, raw inputs, and bulky output
directories must remain outside Git.

Before collecting GB10 evidence, run the local Docker toy smoke:

```sh
scripts/check-docker-toy-benchmarks.sh
```

The smoke runs both tiny ONT and PacBio manifests through the same benchmark
runner and exact-compares the generated `final_clusters.tsv` files to the
committed expected outputs.

For local performance triage before algorithm changes, run:

```sh
scripts/run-local-profiling.sh --output-dir target/local-profile
```

This emits local JSON/TSV profiling reports for tiny ONT and PacBio fixtures
and verifies the `final_clusters.tsv` contract. It is useful for before/after
developer checks but is not GB10 release evidence. See
[`PERFORMANCE_DEEP_DIVE.md`](PERFORMANCE_DEEP_DIVE.md) for ranked optimization
facets and measurement rules.

### Clusters
IsONclust outputs the reads in .fastq file format with each file containing the reads for the respective cluster. The .fastq files are located in the `fastq_files` directory that is created in the given outfolder.

## Contact <a name="contact"></a>
If you encounter any problems, please raise an issue on the issues page, you can also contact the developer of this repository via:
alexander.petri[at]math.su.se


## Credits <a name="credits"></a>

This maintained fork preserves upstream attribution to Alexander J Petri and
Kristoffer Sahlin.

Please cite this study when using isONclust3:

Alexander J Petri, Kristoffer Sahlin, De novo clustering of large long-read transcriptome datasets with isONclust3, Bioinformatics, 2025;, btaf207, [https://doi.org/10.1093/bioinformatics/btaf207](https://doi.org/10.1093/bioinformatics/btaf207).
