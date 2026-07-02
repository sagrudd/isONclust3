#!/usr/bin/env python3
"""Release preflight checks for the maintained isONclust3 fork."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib


REQUIRED_FILES = [
    "AGENTS.md",
    "BENCHMARK_ACCEPTANCE.md",
    "BLOCKERS.md",
    "Dockerfile",
    "MILESTONES.md",
    "OUTPUT_CONTRACTS.md",
    "PERFORMANCE_DEEP_DIVE.md",
    "README.md",
    "RELEASE_CHECKLIST.md",
    "TODO.md",
    "scripts/check-output-contract-fixtures.sh",
    "scripts/check-docker-toy-benchmarks.sh",
    "scripts/run-local-profiling.sh",
    "scripts/run-gb10-benchmark.sh",
]

REQUIRED_TEXT = {
    "AGENTS.md": [
        "Maintain semantic versioning",
        "GB10 benchmark evidence",
        "Do not commit raw sequencing data",
    ],
    "BENCHMARK_ACCEPTANCE.md": [
        "final_clusters.tsv",
        "Container image ID or digest",
        "blocked_pending_data",
    ],
    "BLOCKERS.md": [
        "ISOCLUST-BLOCK-001",
        "ISOCLUST-BLOCK-002",
        "ISOCLUST-BLOCK-003",
        "ISOCLUST-BLOCK-004",
    ],
    "MILESTONES.md": ["Dockerized GB10 Benchmarking"],
    "OUTPUT_CONTRACTS.md": ["<outfolder>/clustering/final_clusters.tsv"],
    "PERFORMANCE_DEEP_DIVE.md": [
        "local-profiling",
        "Ranked Facets",
        "Seed extraction and filtering",
        "Do not mark GB10 blockers resolved",
    ],
    "RELEASE_CHECKLIST.md": [
        "scripts/release-preflight.py --expected-version",
        "scripts/run-local-profiling.sh --case all --include-fastq-output --include-post-cluster",
        "newONform",
    ],
    "TODO.md": ["Dockerized GB10 Evidence", "local profiling harness"],
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_required_files(repo: Path) -> list[str]:
    errors: list[str] = []
    for relative in REQUIRED_FILES:
        path = repo / relative
        if not path.is_file():
            errors.append(f"missing required file: {relative}")
    for relative, markers in REQUIRED_TEXT.items():
        path = repo / relative
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for marker in markers:
            if marker not in text:
                errors.append(f"{relative} missing marker: {marker}")
    return errors


def validate_package_version(repo: Path, expected_version: str | None) -> list[str]:
    manifest = tomllib.loads((repo / "Cargo.toml").read_text(encoding="utf-8"))
    version = manifest.get("package", {}).get("version", "")
    errors = []
    if not re.fullmatch(r"\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?", version):
        errors.append(f"Cargo.toml package.version is not semantic: {version!r}")
    if expected_version and version != expected_version:
        errors.append(
            f"Cargo.toml package.version {version!r} does not match {expected_version!r}"
        )
    return errors


def validate_file_sizes(repo: Path, max_lines: int) -> list[str]:
    errors: list[str] = []
    roots = [repo / "src", repo / "scripts"]
    for root in roots:
        for path in sorted(root.rglob("*")):
            if path.suffix not in {".rs", ".py", ".sh"}:
                continue
            lines = path.read_text(encoding="utf-8").splitlines()
            if len(lines) > max_lines:
                errors.append(f"{path.relative_to(repo)} has {len(lines)} lines")
    return errors


def validate_manifest(repo: Path, path: Path) -> list[str]:
    errors: list[str] = []
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"{path.relative_to(repo)} is invalid JSON: {exc}"]

    required = ["schema_version", "manifest_id", "project", "benchmark_tier", "mode"]
    for key in required:
        if key not in manifest:
            errors.append(f"{path.relative_to(repo)} missing required key: {key}")
    if manifest.get("project") != "isONclust3":
        errors.append(f"{path.relative_to(repo)} project must be isONclust3")
    if manifest.get("mode") not in {"ont", "pacbio"}:
        errors.append(f"{path.relative_to(repo)} mode must be ont or pacbio")

    acceptance = manifest.get("acceptance", {})
    if acceptance.get("requires_gb10_report") is not True:
        errors.append(f"{path.relative_to(repo)} must require a GB10 report")
    if acceptance.get("requires_output_checksums") is not True:
        errors.append(f"{path.relative_to(repo)} must require output checksums")

    for entry in manifest.get("files", []):
        relative = entry.get("path")
        checksum = entry.get("checksum", {})
        if not relative:
            errors.append(f"{path.relative_to(repo)} file entry missing path")
            continue
        file_path = repo / relative
        if not file_path.is_file():
            errors.append(f"{path.relative_to(repo)} references missing file: {relative}")
            continue
        if checksum.get("algorithm") != "sha256":
            errors.append(f"{path.relative_to(repo)} {relative} checksum must be sha256")
            continue
        observed = sha256(file_path)
        expected = checksum.get("value")
        if observed != expected:
            errors.append(
                f"{path.relative_to(repo)} {relative} checksum mismatch: "
                f"{observed} != {expected}"
            )
    return errors


def validate_manifests(repo: Path) -> list[str]:
    manifest_dir = repo / "fixtures" / "manifests"
    manifests = sorted(manifest_dir.glob("*.json"))
    errors: list[str] = []
    if not manifests:
        errors.append("fixtures/manifests contains no benchmark manifests")
    for manifest in manifests:
        errors.extend(validate_manifest(repo, manifest))
    ids = {manifest.stem for manifest in manifests}
    required = {
        "tiny-ont",
        "tiny-pacbio",
        "medium-ont-cdna",
        "phanerognostikon-ont-cdna",
    }
    missing = required - ids
    if missing:
        errors.append(f"missing benchmark manifest(s): {', '.join(sorted(missing))}")
    return errors


def validate_ci(repo: Path) -> list[str]:
    workflow = repo / ".github" / "workflows" / "ci.yml"
    if not workflow.is_file():
        return ["missing .github/workflows/ci.yml"]
    text = workflow.read_text(encoding="utf-8")
    markers = [
        "cargo fmt --check",
        "cargo test",
        "cargo clippy --all-targets -- -D warnings",
        "scripts/check-output-contract-fixtures.sh",
        "scripts/run-local-profiling.sh --case all --include-fastq-output --include-post-cluster",
        "scripts/release-preflight.py",
    ]
    return [f"CI workflow missing marker: {marker}" for marker in markers if marker not in text]


def validate_tracked_artifacts(repo: Path) -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=repo,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    forbidden_prefixes = ("target/", "reports/", "gb10-reports/")
    forbidden_suffixes = (".bam", ".pod5", ".fast5")
    errors = []
    for tracked in result.stdout.splitlines():
        if tracked.startswith(forbidden_prefixes) or tracked.endswith(forbidden_suffixes):
            errors.append(f"forbidden tracked artifact: {tracked}")
    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run isONclust3 release preflight checks.")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--expected-version")
    parser.add_argument("--max-lines", type=int, default=1000)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo = args.repo.resolve()
    errors: list[str] = []
    errors.extend(validate_required_files(repo))
    errors.extend(validate_package_version(repo, args.expected_version))
    errors.extend(validate_file_sizes(repo, args.max_lines))
    errors.extend(validate_manifests(repo))
    errors.extend(validate_ci(repo))
    errors.extend(validate_tracked_artifacts(repo))

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    manifests = len(list((repo / "fixtures" / "manifests").glob("*.json")))
    print(
        "release preflight passed: "
        f"{len(REQUIRED_FILES)} required file(s), "
        f"{manifests} benchmark manifest(s), "
        "package version passed, file-size limits passed, "
        "manifest checksums passed, CI markers passed, artifact hygiene passed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
