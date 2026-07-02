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

It is not release-ready until accepted GB10 reports, generated ``final_clusters.tsv`` producer checksums, and larger-workload profiling evidence are recorded or explicitly waived.

.. toctree::
   :maxdepth: 2

   project-governance
   release-readiness
