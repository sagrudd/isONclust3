# AGENTS.md

## Scope

This repository is the Mnemosyne-maintained fork of `isONclust3`, the upstream
cluster-table producer for `newONform` transcriptome consolidation workflows.

The fork must preserve the upstream command-line contract while making the code
base suitable for reproducible, Dockerized, GB10-aware benchmark evidence and
tight integration with `newONform`.

## Engineering Rules

- Maintain semantic versioning in `Cargo.toml`.
- Keep Rust code modular and hierarchical.
- Avoid source files over 1000 lines.
- Prefer behavior-preserving cleanup before algorithmic changes.
- Preserve `final_clusters.tsv` semantics unless a documented compatibility
  waiver exists; a waiver does not claim accepted producer evidence or
  `newONform` checksum readiness.
- Do not commit raw sequencing data, large generated outputs, Sphinx build
  output, or Python virtual environments/cache artifacts.
- Keep fixtures tiny unless an external manifest records their source and
  checksum.

## Integration Rules

- Treat `newONform` as the downstream consumer of the `final_clusters.tsv`
  contract.
- Any output-format change must update `newONform` fixtures, documentation, and
  equivalence checks in the same release train.
- GB10 benchmark evidence must record command lines, container image identity,
  input checksums, output checksums, wall time, peak memory, thread counts, and
  pass/fail status.

## Documentation Rules

- Maintain Sphinx governance and release-readiness documentation when release
  gates, blockers, benchmark evidence, or downstream handoff rules change.
- Keep `sphinx-build -W -b html docs target/sphinx-html` passing before
  claiming release readiness.

## Git Discipline

- Make surgical commits with focused scope.
- Run focused checks before committing.
- Push after each prompt that modifies repository content.
- Do not stage unrelated dirty files.
