"""Benchmark manifest checks for isONclust3 release preflight."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

REQUIRED_DOWNSTREAM_HANDOFFS = {
    "isonclust3-medium-ont-cdna": "drr138512-final-clusters",
    "isonclust3-phanerognostikon-ont-cdna": "drr178488-final-clusters",
}
REQUIRED_PENDING_EXTERNAL_MANIFESTS = {
    "isonclust3-phanerognostikon-ont-cdna",
}
REQUIRED_ACCEPTED_EXTERNAL_MANIFESTS = {
    "isonclust3-medium-ont-cdna": {
        "source_commit": "8ca0a8ddb8a7250765cb3e6b11e8463c476196b6",
        "tool_version": "0.3.0",
        "run_id": "gb10-medium-drr138512-20260704",
        "container_digest": (
            "sha256:65d2628dbef727f9dd307a7a13cf48506d8225ff7cff187baeea07552d215502"
        ),
        "input_fastq_sha256": (
            "1280e7af119051204874163263b59abbbcf9a9f1a4a9384674b240959029bf03"
        ),
        "final_clusters_sha256": (
            "a37798b916ba5078ca90bed40946ad694bbae957d724034a51e040689406acc7"
        ),
        "final_clusters_bytes": 16380513,
    },
}
REQUIRED_EXTERNAL_PROFILING_FACETS = {
    "final-clusters-contract",
    "minimizer-extraction",
    "quality-filtering",
    "seed-generation",
}
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
REQUIRED_MANIFEST_SCHEMA = "../../schemas/benchmark-fixture.schema.json"
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
    except OSError as exc:
        return [f"{path.relative_to(repo)} is not readable: {exc}"]
    except json.JSONDecodeError as exc:
        return [f"{path.relative_to(repo)} is invalid JSON: {exc}"]
    if not isinstance(manifest, dict):
        return [f"{path.relative_to(repo)} root must be a JSON object"]

    required = [
        "$schema",
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
    if manifest.get("$schema") != REQUIRED_MANIFEST_SCHEMA:
        errors.append(
            f"{path.relative_to(repo)} $schema must be {REQUIRED_MANIFEST_SCHEMA}"
        )
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
    if manifest_id in REQUIRED_PENDING_EXTERNAL_MANIFESTS:
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
    elif manifest_id in REQUIRED_ACCEPTED_EXTERNAL_MANIFESTS:
        expected_evidence = REQUIRED_ACCEPTED_EXTERNAL_MANIFESTS[manifest_id]
        if source.get("availability") != "external_verified":
            errors.append(
                f"{path.relative_to(repo)} source.availability must be external_verified"
            )
        if source.get("blocker_id") is not None:
            errors.append(
                f"{path.relative_to(repo)} source.blocker_id must be omitted once verified"
            )
        if acceptance.get("status") != "accepted_contract":
            errors.append(
                f"{path.relative_to(repo)} acceptance.status must be accepted_contract"
            )
        if acceptance.get("blocker_id") is not None:
            errors.append(
                f"{path.relative_to(repo)} acceptance.blocker_id must be omitted once accepted"
            )
        profiling_plan = manifest.get("profiling_plan")
        if not isinstance(profiling_plan, dict):
            errors.append(f"{path.relative_to(repo)} missing profiling_plan")
        else:
            if profiling_plan.get("blocker_id") != "ISOCLUST-BLOCK-003":
                errors.append(
                    f"{path.relative_to(repo)} profiling_plan.blocker_id must be "
                    "ISOCLUST-BLOCK-003 for accepted producer evidence"
                )
            if profiling_plan.get("status") != "blocked_pending_data":
                errors.append(
                    f"{path.relative_to(repo)} profiling_plan.status must remain "
                    "blocked_pending_data until larger-workload profiling is complete"
                )
        for key, expected_value in expected_evidence.items():
            if acceptance.get(key) != expected_value:
                errors.append(
                    f"{path.relative_to(repo)} acceptance.{key} must be {expected_value}"
                )
        for key in ("gb10_report_path", "gb10_tsv_path"):
            value = acceptance.get(key)
            if not isinstance(value, str) or not value.startswith("/home/stephen/"):
                errors.append(
                    f"{path.relative_to(repo)} acceptance.{key} must cite the GB10 "
                    "artifact path under /home/stephen"
                )
        for key in ("wall_time_seconds", "peak_rss_mb"):
            value = acceptance.get(key)
            if not isinstance(value, (int, float)) or value <= 0:
                errors.append(
                    f"{path.relative_to(repo)} acceptance.{key} must be positive"
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
    file_paths: set[str] = set()
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
            if role in file_roles:
                errors.append(f"{path.relative_to(repo)} duplicate file role: {role}")
            file_roles.add(role)
        relative = entry.get("path")
        checksum = entry.get("checksum", {})
        if not relative:
            errors.append(f"{path.relative_to(repo)} file entry missing path")
            continue
        if isinstance(relative, str):
            if relative in file_paths:
                errors.append(f"{path.relative_to(repo)} duplicate file path: {relative}")
            file_paths.add(relative)
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
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(manifest_data, dict):
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
