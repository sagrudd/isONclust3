"""Benchmark manifest schema checks for isONclust3 release preflight."""

from __future__ import annotations

import json
from pathlib import Path


BENCHMARK_SCHEMA = Path("schemas/benchmark-fixture.schema.json")
BENCHMARK_SCHEMA_REFERENCE = "../../schemas/benchmark-fixture.schema.json"
BENCHMARK_REQUIRED_FIELDS = (
    "$schema",
    "schema_version",
    "manifest_kind",
    "manifest_id",
    "project",
    "benchmark_tier",
    "mode",
    "seeding",
    "source",
    "platform_targets",
    "files",
    "command",
    "acceptance",
)
BENCHMARK_MODES = ("ont", "pacbio")
BENCHMARK_TIERS = ("toy", "medium", "phanerognostikon")
BENCHMARK_SEEDING = ("minimizer", "syncmer")
BENCHMARK_PLATFORMS = ("linux/arm64", "linux/amd64")
BENCHMARK_FILE_ROLES = ("input-fastq", "expected-final-clusters")
BENCHMARK_PROFILING_FACETS = (
    "seed-generation",
    "minimizer-extraction",
    "quality-filtering",
    "final-clusters-contract",
)
BENCHMARK_DOWNSTREAM_IDS = (
    "drr138512-final-clusters",
    "drr178488-final-clusters",
)
BENCHMARK_DEFINITION_KEYS = (
    "checksum",
    "file",
    "profiling_plan",
    "downstream_handoff",
)


def validate_benchmark_schema(repo: Path) -> list[str]:
    path = repo / BENCHMARK_SCHEMA
    errors: list[str] = []
    try:
        schema = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        return [f"{path.relative_to(repo)} is not readable: {exc}"]
    except json.JSONDecodeError as exc:
        return [f"{path.relative_to(repo)} is invalid JSON: {exc}"]
    if not isinstance(schema, dict):
        return [f"{path.relative_to(repo)} root must be a JSON object"]

    expected_root = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://github.com/sagrudd/isONclust3/schemas/benchmark-fixture.schema.json",
        "title": "isONclust3 benchmark fixture manifest",
        "type": "object",
        "additionalProperties": False,
    }
    for key, value in expected_root.items():
        if schema.get(key) != value:
            errors.append(f"{path.relative_to(repo)} {key} must be {value}")
    if schema.get("required") != list(BENCHMARK_REQUIRED_FIELDS):
        errors.append(f"{path.relative_to(repo)} required fields are incomplete")

    properties = schema.get("properties")
    if not isinstance(properties, dict):
        return errors + [f"{path.relative_to(repo)} properties must be an object"]
    for field in BENCHMARK_REQUIRED_FIELDS:
        if field not in properties:
            errors.append(f"{path.relative_to(repo)} properties missing {field}")
    _validate_root_properties(path, repo, properties, errors)

    definitions = schema.get("$defs")
    if not isinstance(definitions, dict):
        return errors + [f"{path.relative_to(repo)} $defs must be an object"]
    if tuple(definitions) != BENCHMARK_DEFINITION_KEYS:
        errors.append(f"{path.relative_to(repo)} $defs keys must follow schema order")
    _validate_checksum_definition(path, repo, definitions.get("checksum"), errors)
    _validate_file_definition(path, repo, definitions.get("file"), errors)
    _validate_profiling_plan_definition(
        path, repo, definitions.get("profiling_plan"), errors
    )
    _validate_downstream_handoff_definition(
        path, repo, definitions.get("downstream_handoff"), errors
    )
    errors.extend(_validate_manifest_keys_against_schema(repo, schema))
    return errors


def _validate_root_properties(
    path: Path, repo: Path, properties: dict[str, object], errors: list[str]
) -> None:
    expected_consts = {
        "$schema": BENCHMARK_SCHEMA_REFERENCE,
        "schema_version": 1,
        "manifest_kind": "isonclust3-benchmark-fixture",
        "project": "isONclust3",
    }
    for field, value in expected_consts.items():
        field_property = properties.get(field)
        if not isinstance(field_property, dict) or field_property.get("const") != value:
            errors.append(f"{path.relative_to(repo)} properties.{field}.const must be {value}")
    expected_enums = {
        "benchmark_tier": list(BENCHMARK_TIERS),
        "mode": list(BENCHMARK_MODES),
        "seeding": list(BENCHMARK_SEEDING),
    }
    for field, values in expected_enums.items():
        field_property = properties.get(field)
        if not isinstance(field_property, dict) or field_property.get("enum") != values:
            errors.append(f"{path.relative_to(repo)} properties.{field}.enum is incomplete")
    manifest_id = properties.get("manifest_id")
    if not isinstance(manifest_id, dict) or manifest_id.get("pattern") != "^isonclust3-[a-z0-9-]+$":
        errors.append(f"{path.relative_to(repo)} manifest_id must require isONclust3 IDs")
    platforms = properties.get("platform_targets")
    if not isinstance(platforms, dict) or platforms.get("uniqueItems") is not True:
        errors.append(f"{path.relative_to(repo)} platform_targets must be unique")
    elif platforms.get("items", {}).get("enum") != list(BENCHMARK_PLATFORMS):
        errors.append(f"{path.relative_to(repo)} platform target enum is incomplete")
    command = properties.get("command")
    if not isinstance(command, dict):
        errors.append(f"{path.relative_to(repo)} command must be an object")
    else:
        command_properties = command.get("properties", {})
        image = command_properties.get("container_image", {})
        args = command_properties.get("args", {})
        if image.get("const") != "isonclust3:gb10":
            errors.append(f"{path.relative_to(repo)} command image must be isonclust3:gb10")
        if args.get("type") != "array" or args.get("minItems") != 9:
            errors.append(f"{path.relative_to(repo)} command args must be a populated array")


def _validate_checksum_definition(
    path: Path, repo: Path, definition: object, errors: list[str]
) -> None:
    if not isinstance(definition, dict):
        errors.append(f"{path.relative_to(repo)} $defs.checksum must be an object")
        return
    properties = definition.get("properties", {})
    algorithm = properties.get("algorithm", {})
    value = properties.get("value", {})
    if algorithm.get("const") != "sha256":
        errors.append(f"{path.relative_to(repo)} checksum algorithm must be sha256")
    if value.get("pattern") != "^[0-9a-f]{64}$":
        errors.append(f"{path.relative_to(repo)} checksum value must gate sha256 hex")


def _validate_file_definition(
    path: Path, repo: Path, definition: object, errors: list[str]
) -> None:
    if not isinstance(definition, dict):
        errors.append(f"{path.relative_to(repo)} $defs.file must be an object")
        return
    if definition.get("required") != ["path", "role", "checksum"]:
        errors.append(f"{path.relative_to(repo)} file required fields are incomplete")
    properties = definition.get("properties", {})
    role = properties.get("role", {})
    checksum = properties.get("checksum", {})
    if role.get("enum") != list(BENCHMARK_FILE_ROLES):
        errors.append(f"{path.relative_to(repo)} file role enum is incomplete")
    if checksum.get("$ref") != "#/$defs/checksum":
        errors.append(f"{path.relative_to(repo)} file checksum must reference checksum def")


def _validate_profiling_plan_definition(
    path: Path, repo: Path, definition: object, errors: list[str]
) -> None:
    if not isinstance(definition, dict):
        errors.append(f"{path.relative_to(repo)} $defs.profiling_plan must be an object")
        return
    properties = definition.get("properties", {})
    if properties.get("scope", {}).get("const") != "smallest-accepted-larger-workload":
        errors.append(f"{path.relative_to(repo)} profiling scope must be fixed")
    if properties.get("status", {}).get("const") != "blocked_pending_data":
        errors.append(f"{path.relative_to(repo)} profiling status must stay blocked")
    facets = properties.get("required_facets", {}).get("items", {})
    if facets.get("enum") != list(BENCHMARK_PROFILING_FACETS):
        errors.append(f"{path.relative_to(repo)} profiling facets enum is incomplete")


def _validate_downstream_handoff_definition(
    path: Path, repo: Path, definition: object, errors: list[str]
) -> None:
    if not isinstance(definition, dict):
        errors.append(f"{path.relative_to(repo)} $defs.downstream_handoff must be an object")
        return
    properties = definition.get("properties", {})
    if properties.get("consumer", {}).get("const") != "newONform":
        errors.append(f"{path.relative_to(repo)} downstream consumer must be newONform")
    if properties.get("consumer_blocker_id", {}).get("const") != "NOF-BLOCK-006":
        errors.append(f"{path.relative_to(repo)} downstream blocker must be NOF-BLOCK-006")
    generated_input = properties.get("generated_input_id", {})
    if generated_input.get("enum") != list(BENCHMARK_DOWNSTREAM_IDS):
        errors.append(f"{path.relative_to(repo)} downstream generated IDs are incomplete")


def _validate_manifest_keys_against_schema(repo: Path, schema: dict[str, object]) -> list[str]:
    errors: list[str] = []
    properties = schema.get("properties", {})
    definitions = schema.get("$defs", {})
    if not isinstance(properties, dict) or not isinstance(definitions, dict):
        return errors

    manifest_paths = sorted((repo / "fixtures" / "manifests").glob("*.json"))
    allowed_root_keys = set(properties)
    required_root_keys = set(BENCHMARK_REQUIRED_FIELDS)
    for manifest_path in manifest_paths:
        relative = manifest_path.relative_to(repo)
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except OSError as exc:
            errors.append(f"{relative} is not readable: {exc}")
            continue
        except json.JSONDecodeError as exc:
            errors.append(f"{relative} is invalid JSON: {exc}")
            continue
        if not isinstance(manifest, dict):
            errors.append(f"{relative} root must be a JSON object")
            continue

        missing = required_root_keys - set(manifest)
        if missing:
            errors.append(f"{relative} missing schema-required keys: {', '.join(sorted(missing))}")
        unexpected = set(manifest) - allowed_root_keys
        if unexpected:
            errors.append(f"{relative} has keys outside benchmark schema: {', '.join(sorted(unexpected))}")
        _validate_nested_object_keys(relative, "source", manifest.get("source"), properties, errors)
        _validate_nested_object_keys(relative, "command", manifest.get("command"), properties, errors)
        _validate_nested_object_keys(
            relative, "acceptance", manifest.get("acceptance"), properties, errors
        )
        if "profiling_plan" in manifest:
            _validate_definition_object_keys(
                relative,
                "profiling_plan",
                manifest.get("profiling_plan"),
                definitions.get("profiling_plan"),
                errors,
            )
        if "downstream_handoff" in manifest:
            _validate_definition_object_keys(
                relative,
                "downstream_handoff",
                manifest.get("downstream_handoff"),
                definitions.get("downstream_handoff"),
                errors,
            )
        file_definition = definitions.get("file")
        files = manifest.get("files")
        if isinstance(files, list):
            for index, entry in enumerate(files):
                _validate_definition_object_keys(
                    relative, f"files[{index}]", entry, file_definition, errors
                )
                if isinstance(entry, dict):
                    _validate_definition_object_keys(
                        relative,
                        f"files[{index}].checksum",
                        entry.get("checksum"),
                        definitions.get("checksum"),
                        errors,
                    )
    return errors


def _validate_nested_object_keys(
    manifest_path: Path,
    field: str,
    value: object,
    properties: dict[str, object],
    errors: list[str],
) -> None:
    schema_property = properties.get(field)
    if not isinstance(schema_property, dict):
        return
    allowed = _schema_property_keys(schema_property)
    required = set(schema_property.get("required", []))
    _validate_key_set(manifest_path, field, value, allowed, required, errors)


def _validate_definition_object_keys(
    manifest_path: Path,
    field: str,
    value: object,
    definition: object,
    errors: list[str],
) -> None:
    if not isinstance(definition, dict):
        return
    allowed = _schema_property_keys(definition)
    required = set(definition.get("required", []))
    _validate_key_set(manifest_path, field, value, allowed, required, errors)


def _schema_property_keys(schema_object: dict[str, object]) -> set[str]:
    properties = schema_object.get("properties", {})
    return set(properties) if isinstance(properties, dict) else set()


def _validate_key_set(
    manifest_path: Path,
    field: str,
    value: object,
    allowed: set[str],
    required: set[str],
    errors: list[str],
) -> None:
    if not isinstance(value, dict):
        return
    missing = required - set(value)
    if missing:
        errors.append(f"{manifest_path} {field} missing schema-required keys: {', '.join(sorted(missing))}")
    unexpected = set(value) - allowed
    if unexpected:
        errors.append(f"{manifest_path} {field} has keys outside benchmark schema: {', '.join(sorted(unexpected))}")
