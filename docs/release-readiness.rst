Release Readiness
=================

``isONclust3`` release readiness is controlled by the root governance files and
the Dockerized GB10 benchmark evidence path.

Minimum Local Checks
--------------------

- ``cargo fmt --check``
- ``cargo test --quiet``
- ``cargo clippy --all-targets -- -D warnings``
- ``scripts/check-output-contract-fixtures.sh``
- ``scripts/run-local-profiling.sh --case all --include-fastq-output --include-post-cluster --include-gff``
- ``sphinx-build -W -b html docs target/sphinx-html``
- ``scripts/release-preflight.py --expected-version 0.3.0``
- ``scripts/check-docker-toy-benchmarks.sh``

Current High-Priority Blockers
------------------------------

- ``ISOCLUST-BLOCK-001``: accepted GB10 benchmark reports are still required.
- ``ISOCLUST-BLOCK-002``: medium and Phanerognostikon generated
  ``final_clusters.tsv`` producer checksums are still required for
  ``newONform``.
- ``ISOCLUST-BLOCK-003``: accepted larger-workload profiling evidence is still
  required before further algorithmic optimization claims.

Waivers must name the blocker, workload, available evidence, downstream
``newONform`` impact, and expiry condition. A waiver narrows release scope; it
does not claim accepted GB10 producer evidence or generated
``final_clusters.tsv`` checksum readiness.

Downstream Handoff
------------------

Accepted producer evidence must update ``newONform`` in the same release train:
the ``external/isONclust3`` submodule, generated-input registers, blockers, and
documentation must all cite the accepted upstream commit and generated
``final_clusters.tsv`` checksums.
