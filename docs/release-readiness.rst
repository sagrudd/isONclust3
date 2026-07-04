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

- ``ISOCLUST-BLOCK-001``: accepted Phanerognostikon GB10 benchmark reports are
  still required. Toy ONT and toy PacBio GB10 contract reports are accepted for
  source commit ``3ba608e3fa87d855f11d75e3c77556f2dd6b1a59`` and tool version
  ``0.3.0`` under
  ``/home/stephen/gb10-verification-20260704/results/isONclust3-provenance/``.
  Medium DRR138512 GB10 contract evidence is accepted for source commit
  ``8ca0a8ddb8a7250765cb3e6b11e8463c476196b6`` under
  ``/home/stephen/gb10-verification-20260704/results/isONclust3-medium-drr138512/``.
- ``ISOCLUST-BLOCK-002``: the Phanerognostikon generated
  ``final_clusters.tsv`` producer checksum is still required for
  ``newONform``; medium DRR138512 is accepted with checksum
  ``a37798b916ba5078ca90bed40946ad694bbae957d724034a51e040689406acc7``.
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
