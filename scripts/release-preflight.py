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
    "OPTIMIZATION_EVIDENCE.md",
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
    "OPTIMIZATION_EVIDENCE.md": [
        "Raw local reports must not be committed",
        "scripts/run-local-profiling.sh --case all --include-fastq-output --include-post-cluster --include-gff",
        "ISOCLUST-BLOCK-001",
        "ISOCLUST-BLOCK-003",
    ],
    "OUTPUT_CONTRACTS.md": ["<outfolder>/clustering/final_clusters.tsv"],
    "PERFORMANCE_DEEP_DIVE.md": [
        "local-profiling",
        "Ranked Facets",
        "Seed extraction and filtering",
        "Do not mark GB10 blockers resolved",
    ],
    "RELEASE_CHECKLIST.md": [
        "scripts/release-preflight.py --expected-version",
        "scripts/run-local-profiling.sh --case all --include-fastq-output --include-post-cluster --include-gff",
        "newONform",
    ],
    "TODO.md": ["Dockerized GB10 Evidence", "local profiling harness"],
}

REQUIRED_DOWNSTREAM_HANDOFFS = {
    "isonclust3-medium-ont-cdna": "drr138512-final-clusters",
    "isonclust3-phanerognostikon-ont-cdna": "drr178488-final-clusters",
}
REQUIRED_BLOCKED_EXTERNAL_MANIFESTS = {
    "isonclust3-medium-ont-cdna",
    "isonclust3-phanerognostikon-ont-cdna",
}
REQUIRED_EXTERNAL_PROFILING_FACETS = {
    "final-clusters-contract",
    "minimizer-extraction",
    "quality-filtering",
    "seed-generation",
}
REQUIRED_OPTIMIZATION_ENTRY_MARKERS = (
    "- Date:",
    "- Optimized facet:",
    "- Compatibility risk:",
    "- Before command:",
    "- Before report path:",
    "- After command:",
    "- After report path:",
    "- Contract checks run:",
    "- GB10 or larger-workload status:",
)
REQUIRED_OPTIMIZATION_CONTRACT_MARKERS = (
    "cargo fmt --check",
    "cargo test --quiet",
    "cargo clippy --all-targets -- -D warnings",
    "scripts/check-output-contract-fixtures.sh",
    "scripts/release-preflight.py --expected-version 0.3.0",
)
REQUIRED_OPTIMIZATION_COMMAND_MARKER = "scripts/run-local-profiling.sh"
REQUIRED_OPTIMIZATION_REPORT_PATH_MARKER = "`target/local-profile/`"
REQUIRED_RELEASE_CHECKLIST_SECTIONS = (
    "## Required Local Checks",
    "## Required Docker And GB10 Evidence",
    "## Required Integration Evidence",
)
REQUIRED_BENCHMARK_TIERS = {
    "medium",
    "phanerognostikon",
    "toy",
}
REQUIRED_MANIFEST_STEMS = {
    "medium-ont-cdna",
    "phanerognostikon-ont-cdna",
    "tiny-ont",
    "tiny-pacbio",
}
REQUIRED_PLATFORM_TARGETS = {
    "linux/amd64",
    "linux/arm64",
}
REQUIRED_FILE_ROLES = {
    "expected-final-clusters",
    "input-fastq",
}
REQUIRED_TOY_FILE_ROLES = {
    "expected-final-clusters",
    "input-fastq",
}
REQUIRED_COMMAND_FLAGS = {
    "--fastq",
    "--mode",
    "--outfolder",
    "--seeding",
    "--no-fastq",
}
REQUIRED_COMMAND_VALUES = {
    "--fastq": "/work/data/reads.fastq",
    "--outfolder": "/work/out/isonclust3",
}
SHA256_HEX_PATTERN = re.compile(r"[0-9a-f]{64}")


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


def command_value(args: list[str], flag: str) -> str | None:
    try:
        index = args.index(flag)
    except ValueError:
        return None
    value_index = index + 1
    if value_index >= len(args):
        return None
    return args[value_index]


def validate_manifest(repo: Path, path: Path) -> list[str]:
    errors: list[str] = []
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"{path.relative_to(repo)} is invalid JSON: {exc}"]

    required = [
        "schema_version",
        "manifest_kind",
        "manifest_id",
        "project",
        "benchmark_tier",
        "mode",
        "seeding",
    ]
    for key in required:
        if key not in manifest:
            errors.append(f"{path.relative_to(repo)} missing required key: {key}")
    expected_manifest_id = f"isonclust3-{path.stem}"
    if manifest.get("manifest_id") != expected_manifest_id:
        errors.append(
            f"{path.relative_to(repo)} manifest_id must be {expected_manifest_id}"
        )
    if manifest.get("schema_version") != 1:
        errors.append(f"{path.relative_to(repo)} schema_version must be 1")
    if manifest.get("manifest_kind") != "isonclust3-benchmark-fixture":
        errors.append(
            f"{path.relative_to(repo)} manifest_kind must be isonclust3-benchmark-fixture"
        )
    if manifest.get("project") != "isONclust3":
        errors.append(f"{path.relative_to(repo)} project must be isONclust3")
    if manifest.get("benchmark_tier") not in REQUIRED_BENCHMARK_TIERS:
        expected = ", ".join(sorted(REQUIRED_BENCHMARK_TIERS))
        errors.append(f"{path.relative_to(repo)} benchmark_tier must be one of {expected}")
    if manifest.get("mode") not in {"ont", "pacbio"}:
        errors.append(f"{path.relative_to(repo)} mode must be ont or pacbio")
    if manifest.get("seeding") not in {"minimizer", "syncmer"}:
        errors.append(f"{path.relative_to(repo)} seeding must be minimizer or syncmer")
    platform_targets = manifest.get("platform_targets")
    if not isinstance(platform_targets, list) or "linux/arm64" not in platform_targets:
        errors.append(f"{path.relative_to(repo)} platform_targets must include linux/arm64")
    elif not all(isinstance(target, str) for target in platform_targets):
        errors.append(f"{path.relative_to(repo)} platform_targets must be a string list")
    else:
        unexpected_targets = set(platform_targets) - REQUIRED_PLATFORM_TARGETS
        if unexpected_targets:
            expected_targets = ", ".join(sorted(REQUIRED_PLATFORM_TARGETS))
            errors.append(
                f"{path.relative_to(repo)} platform_targets must be one of "
                f"{expected_targets}"
            )

    source = manifest.get("source")
    if not isinstance(source, dict):
        errors.append(f"{path.relative_to(repo)} source must be an object")
        source = {}
    description = source.get("description")
    if not isinstance(description, str) or not description.strip():
        errors.append(f"{path.relative_to(repo)} source.description must be populated")
    if manifest.get("benchmark_tier") == "toy" and source.get("license") != "GPL-3.0-only":
        errors.append(f"{path.relative_to(repo)} toy source.license must be GPL-3.0-only")

    acceptance = manifest.get("acceptance")
    if not isinstance(acceptance, dict):
        errors.append(f"{path.relative_to(repo)} acceptance must be an object")
        acceptance = {}
    if acceptance.get("requires_gb10_report") is not True:
        errors.append(f"{path.relative_to(repo)} must require a GB10 report")
    if acceptance.get("requires_container_digest") is not True:
        errors.append(f"{path.relative_to(repo)} must require a container digest")
    if acceptance.get("requires_output_checksums") is not True:
        errors.append(f"{path.relative_to(repo)} must require output checksums")

    command = manifest.get("command", {})
    if not isinstance(command, dict):
        errors.append(f"{path.relative_to(repo)} command must be an object")
    else:
        if command.get("container_image") != "isonclust3:gb10":
            errors.append(
                f"{path.relative_to(repo)} command.container_image must be isonclust3:gb10"
            )
        args = command.get("args")
        if not isinstance(args, list) or not all(isinstance(arg, str) for arg in args):
            errors.append(f"{path.relative_to(repo)} command.args must be a string list")
        else:
            missing_flags = REQUIRED_COMMAND_FLAGS.difference(args)
            if missing_flags:
                errors.append(
                    f"{path.relative_to(repo)} command.args missing flags: "
                    f"{', '.join(sorted(missing_flags))}"
                )
            observed_flags = {arg for arg in args if arg.startswith("--")}
            unexpected_flags = observed_flags - REQUIRED_COMMAND_FLAGS
            if unexpected_flags:
                errors.append(
                    f"{path.relative_to(repo)} command.args unexpected flags: "
                    f"{', '.join(sorted(unexpected_flags))}"
                )
            for flag in sorted(REQUIRED_COMMAND_FLAGS):
                occurrences = args.count(flag)
                if occurrences != 1:
                    errors.append(
                        f"{path.relative_to(repo)} command.args {flag} "
                        f"must appear exactly once"
                    )
            expected_args = [
                "--fastq",
                REQUIRED_COMMAND_VALUES["--fastq"],
                "--mode",
                str(manifest.get("mode")),
                "--outfolder",
                REQUIRED_COMMAND_VALUES["--outfolder"],
                "--seeding",
                str(manifest.get("seeding")),
                "--no-fastq",
            ]
            if args != expected_args:
                errors.append(
                    f"{path.relative_to(repo)} command.args must match the "
                    "canonical file-based handoff sequence"
                )
            expected_values = {
                **REQUIRED_COMMAND_VALUES,
                "--mode": str(manifest.get("mode")),
                "--seeding": str(manifest.get("seeding")),
            }
            for flag, expected_value in expected_values.items():
                observed = command_value(args, flag)
                if observed != expected_value:
                    errors.append(
                        f"{path.relative_to(repo)} command.args {flag} "
                        f"must be followed by {expected_value}"
                    )

    manifest_id = manifest.get("manifest_id")
    if manifest_id in REQUIRED_BLOCKED_EXTERNAL_MANIFESTS:
        if source.get("availability") != "external_pending":
            errors.append(
                f"{path.relative_to(repo)} source.availability must be external_pending"
            )
        if source.get("blocker_id") != "ISOCLUST-BLOCK-002":
            errors.append(
                f"{path.relative_to(repo)} source.blocker_id must be ISOCLUST-BLOCK-002"
            )
        if acceptance.get("status") != "blocked_pending_data":
            errors.append(
                f"{path.relative_to(repo)} acceptance.status must be blocked_pending_data"
            )
        if acceptance.get("blocker_id") != "ISOCLUST-BLOCK-002":
            errors.append(
                f"{path.relative_to(repo)} acceptance.blocker_id must be ISOCLUST-BLOCK-002"
            )
        profiling_plan = manifest.get("profiling_plan")
        if not isinstance(profiling_plan, dict):
            errors.append(f"{path.relative_to(repo)} missing profiling_plan")
        else:
            if profiling_plan.get("scope") != "smallest-accepted-larger-workload":
                errors.append(
                    f"{path.relative_to(repo)} profiling_plan.scope must be "
                    "smallest-accepted-larger-workload"
                )
            if profiling_plan.get("status") != "blocked_pending_data":
                errors.append(
                    f"{path.relative_to(repo)} profiling_plan.status must be "
                    "blocked_pending_data"
                )
            if profiling_plan.get("blocker_id") != "ISOCLUST-BLOCK-002":
                errors.append(
                    f"{path.relative_to(repo)} profiling_plan.blocker_id must be "
                    "ISOCLUST-BLOCK-002"
                )
            facets = profiling_plan.get("required_facets")
            if not isinstance(facets, list) or not all(
                isinstance(facet, str) for facet in facets
            ):
                errors.append(
                    f"{path.relative_to(repo)} profiling_plan.required_facets "
                    "must be a string list"
                )
            else:
                missing_facets = REQUIRED_EXTERNAL_PROFILING_FACETS - set(facets)
                if missing_facets:
                    errors.append(
                        f"{path.relative_to(repo)} profiling_plan.required_facets "
                        f"missing: {', '.join(sorted(missing_facets))}"
                    )

    if manifest_id in REQUIRED_DOWNSTREAM_HANDOFFS:
        handoff = manifest.get("downstream_handoff")
        if not isinstance(handoff, dict):
            errors.append(f"{path.relative_to(repo)} missing downstream_handoff")
        else:
            expected_input_id = REQUIRED_DOWNSTREAM_HANDOFFS[manifest_id]
            expected = {
                "consumer": "newONform",
                "generated_input_register": "fixtures/generated-inputs/register.json",
                "generated_input_id": expected_input_id,
                "consumer_blocker_id": "NOF-BLOCK-006",
            }
            for key, value in expected.items():
                if handoff.get(key) != value:
                    errors.append(
                        f"{path.relative_to(repo)} downstream_handoff.{key} "
                        f"must be {value}"
                    )

    files = manifest.get("files")
    if not isinstance(files, list):
        errors.append(f"{path.relative_to(repo)} files must be a list")
        files = []

    file_roles: set[str] = set()
    for entry in files:
        if not isinstance(entry, dict):
            errors.append(f"{path.relative_to(repo)} file entry must be an object")
            continue
        role = entry.get("role")
        if role not in REQUIRED_FILE_ROLES:
            expected_roles = ", ".join(sorted(REQUIRED_FILE_ROLES))
            errors.append(
                f"{path.relative_to(repo)} file entry role must be one of "
                f"{expected_roles}"
            )
        elif isinstance(role, str):
            file_roles.add(role)
        relative = entry.get("path")
        checksum = entry.get("checksum", {})
        if not relative:
            errors.append(f"{path.relative_to(repo)} file entry missing path")
            continue
        if manifest.get("benchmark_tier") == "toy" and isinstance(role, str):
            expected_paths = {
                "expected-final-clusters": (
                    f"fixtures/tiny/{manifest.get('mode')}/expected/final_clusters.tsv"
                ),
                "input-fastq": f"fixtures/tiny/{manifest.get('mode')}/reads.fastq",
            }
            expected_path = expected_paths.get(role)
            if expected_path and relative != expected_path:
                errors.append(
                    f"{path.relative_to(repo)} {role} path must be {expected_path}"
                )
        file_path = repo / relative
        if not file_path.is_file():
            errors.append(f"{path.relative_to(repo)} references missing file: {relative}")
            continue
        if checksum.get("algorithm") != "sha256":
            errors.append(f"{path.relative_to(repo)} {relative} checksum must be sha256")
            continue
        expected = checksum.get("value")
        if not isinstance(expected, str) or not SHA256_HEX_PATTERN.fullmatch(expected):
            errors.append(
                f"{path.relative_to(repo)} {relative} checksum value must be "
                "64 lowercase hex characters"
            )
            continue
        observed = sha256(file_path)
        if observed != expected:
            errors.append(
                f"{path.relative_to(repo)} {relative} checksum mismatch: "
                f"{observed} != {expected}"
            )
    if manifest.get("benchmark_tier") == "toy":
        missing_roles = REQUIRED_TOY_FILE_ROLES - file_roles
        if missing_roles:
            errors.append(
                f"{path.relative_to(repo)} missing toy file role(s): "
                f"{', '.join(sorted(missing_roles))}"
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
    stems = {manifest.stem for manifest in manifests}
    missing = REQUIRED_MANIFEST_STEMS - stems
    if missing:
        errors.append(f"missing benchmark manifest(s): {', '.join(sorted(missing))}")
    unexpected = stems - REQUIRED_MANIFEST_STEMS
    if unexpected:
        errors.append(
            f"unexpected benchmark manifest(s): {', '.join(sorted(unexpected))}"
        )

    observed_ids: dict[str, Path] = {}
    for manifest in manifests:
        try:
            manifest_data = json.loads(manifest.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        manifest_id = manifest_data.get("manifest_id")
        if not isinstance(manifest_id, str):
            continue
        duplicate = observed_ids.get(manifest_id)
        if duplicate:
            errors.append(
                f"duplicate benchmark manifest_id {manifest_id}: "
                f"{duplicate.relative_to(repo)} and {manifest.relative_to(repo)}"
            )
        observed_ids[manifest_id] = manifest
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
        "scripts/run-local-profiling.sh --case all --include-fastq-output --include-post-cluster --include-gff",
        "scripts/release-preflight.py",
    ]
    return [f"CI workflow missing marker: {marker}" for marker in markers if marker not in text]


def validate_optimization_evidence(repo: Path) -> list[str]:
    path = repo / "OPTIMIZATION_EVIDENCE.md"
    text = path.read_text(encoding="utf-8")
    entry_matches = list(re.finditer(r"^### (?P<title>.+)$", text, flags=re.MULTILINE))
    if not entry_matches:
        return ["OPTIMIZATION_EVIDENCE.md must include at least one evidence entry"]

    errors: list[str] = []
    for index, match in enumerate(entry_matches):
        title = match.group("title")
        start = match.end()
        end = entry_matches[index + 1].start() if index + 1 < len(entry_matches) else len(text)
        entry_text = text[start:end]
        sha = title.split(" ", 1)[0]
        if not re.fullmatch(r"[0-9a-f]{40}", sha):
            errors.append(
                f"OPTIMIZATION_EVIDENCE.md entry {title!r} must start with a "
                "40-character lowercase Git SHA"
            )
        else:
            result = subprocess.run(
                ["git", "cat-file", "-e", f"{sha}^{{commit}}"],
                cwd=repo,
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            if result.returncode != 0:
                errors.append(
                    f"OPTIMIZATION_EVIDENCE.md entry {sha} does not resolve "
                    "to a commit"
                )
            else:
                ancestor = subprocess.run(
                    ["git", "merge-base", "--is-ancestor", sha, "HEAD"],
                    cwd=repo,
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                if ancestor.returncode != 0:
                    errors.append(
                        f"OPTIMIZATION_EVIDENCE.md entry {sha} is not reachable "
                        "from HEAD"
                    )
        for marker in REQUIRED_OPTIMIZATION_ENTRY_MARKERS:
            if marker not in entry_text:
                errors.append(f"OPTIMIZATION_EVIDENCE.md entry {sha} missing {marker}")
        for marker in REQUIRED_OPTIMIZATION_CONTRACT_MARKERS:
            if marker not in entry_text:
                errors.append(
                    f"OPTIMIZATION_EVIDENCE.md entry {sha} missing contract "
                    f"check marker: {marker}"
                )
        command_count = entry_text.count(REQUIRED_OPTIMIZATION_COMMAND_MARKER)
        if command_count < 2:
            errors.append(
                f"OPTIMIZATION_EVIDENCE.md entry {sha} must cite before and "
                "after local profiling commands"
            )
        report_path_count = entry_text.count(REQUIRED_OPTIMIZATION_REPORT_PATH_MARKER)
        if report_path_count < 2:
            errors.append(
                f"OPTIMIZATION_EVIDENCE.md entry {sha} must cite ignored "
                "before and after target/local-profile/ report paths"
            )
    return errors


def validate_release_checklist(repo: Path) -> list[str]:
    path = repo / "RELEASE_CHECKLIST.md"
    text = path.read_text(encoding="utf-8")
    errors = [
        f"RELEASE_CHECKLIST.md missing section: {section}"
        for section in REQUIRED_RELEASE_CHECKLIST_SECTIONS
        if section not in text
    ]
    checked_items = [
        (line_number, line)
        for line_number, line in enumerate(text.splitlines(), start=1)
        if re.match(r"- \[[xX]\]", line)
    ]
    for line_number, line in checked_items:
        errors.append(
            f"RELEASE_CHECKLIST.md line {line_number} must remain unchecked "
            f"until release evidence is collected: {line}"
        )
    unchecked_items = [line for line in text.splitlines() if line.startswith("- [ ]")]
    if len(unchecked_items) < 10:
        errors.append("RELEASE_CHECKLIST.md must keep the operator checklist populated")
    return errors


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
    errors.extend(validate_optimization_evidence(repo))
    errors.extend(validate_release_checklist(repo))
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
