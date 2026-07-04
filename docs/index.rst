isONclust3 Maintained Fork
==========================

``isONclust3`` is the upstream cluster-table producer used by ``newONform`` for
transcriptome consolidation. The maintained fork preserves the original command
surface while adding release governance, ``final_clusters.tsv`` contract
fixtures, and Dockerized GB10-aware benchmark gates.

Current Status
--------------

Implemented release-candidate foundation includes strict Rust lint/format
hygiene, tiny ONT/PacBio output-contract fixtures, local profiling automation,
Dockerized benchmark manifests, a GB10 benchmark runner, and explicit
``newONform`` handoff documentation.

Current accepted GB10 reports and generated ``final_clusters.tsv`` producer checksums
are recorded for toy, medium, and Phanerognostikon workloads. It is not
release-ready until larger-workload profiling evidence is recorded. Any explicit waiver must stay visible as a scoped release limitation and must not claim accepted GB10 producer evidence or generated ``final_clusters.tsv`` checksum readiness for ``newONform``.

.. toctree::
   :maxdepth: 2

   project-governance
   release-readiness
