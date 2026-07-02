#!/usr/bin/env python3
"""Release preflight checks for the maintained isONclust3 fork."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from preflight_artifacts import validate_tracked_artifacts
from preflight_benchmark_schema import validate_benchmark_schema
from preflight_ci import validate_ci
from preflight_gb10_runner import validate_gb10_runner
from preflight_governance import (
    REQUIRED_ACTIVE_BLOCKERS,
    validate_benchmark_acceptance,
    validate_blockers,
)
from preflight_manifests import validate_manifests
from preflight_output_contracts import validate_output_contract_register
from preflight_optimization_evidence import validate_optimization_evidence
from preflight_release_checklist import validate_release_checklist
from preflight_required_files import REQUIRED_FILES, validate_required_files

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib


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
    errors.extend(validate_blockers(repo))
    errors.extend(validate_benchmark_acceptance(repo))
    errors.extend(validate_package_version(repo, args.expected_version))
    errors.extend(validate_file_sizes(repo, args.max_lines))
    errors.extend(validate_benchmark_schema(repo))
    errors.extend(validate_output_contract_register(repo))
    errors.extend(validate_gb10_runner(repo))
    errors.extend(validate_manifests(repo))
    errors.extend(validate_ci(repo))
    errors.extend(validate_optimization_evidence(repo))
    errors.extend(validate_release_checklist(repo, REQUIRED_ACTIVE_BLOCKERS))
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
        "benchmark schema passed, output contract register passed, "
        "manifest checksums passed, "
        "CI markers passed, artifact hygiene passed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
