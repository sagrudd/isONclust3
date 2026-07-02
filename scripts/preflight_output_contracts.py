"""Output-contract register checks for isONclust3 release preflight."""

from __future__ import annotations

import json
import re
from pathlib import Path


REQUIRED_OUTPUT_CONTRACT_ENTRIES = {
    "isonclust3-tiny-ont-final-clusters": {
        "mode": "ont",
        "run_path": "fixtures/tiny/ont/expected/final_clusters.tsv",
        "fastq_path": "fixtures/tiny/ont/reads.fastq",
    },
    "isonclust3-gff-tiny-ont-final-clusters": {
        "mode": "ont",
        "run_path": "fixtures/tiny/ont/expected/gff_final_clusters.tsv",
        "fastq_path": "fixtures/tiny/ont/reads.fastq",
    },
    "isonclust3-tiny-pacbio-final-clusters": {
        "mode": "pacbio",
        "run_path": "fixtures/tiny/pacbio/expected/final_clusters.tsv",
        "fastq_path": "fixtures/tiny/pacbio/reads.fastq",
    },
    "isonclust3-gff-tiny-pacbio-final-clusters": {
        "mode": "pacbio",
        "run_path": "fixtures/tiny/pacbio/expected/gff_final_clusters.tsv",
        "fastq_path": "fixtures/tiny/pacbio/reads.fastq",
    },
}
REQUIRED_OUTPUT_CONTRACT_ENTRY_IDS = tuple(REQUIRED_OUTPUT_CONTRACT_ENTRIES)
SHA256_HEX_PATTERN = re.compile(r"[0-9a-f]{64}")
OUTPUT_CONTRACT_REGISTER = Path("fixtures/output-contracts/final-clusters-register.json")
OUTPUT_CONTRACT_SCHEMA = Path("schemas/output-contract-register.schema.json")
OUTPUT_CONTRACT_SCHEMA_REFERENCE = "../../schemas/output-contract-register.schema.json"
OUTPUT_CONTRACT_RELATIVE_PATH_PATTERN = r"^(?!/)(?!.*(?:^|/)\.\.(?:/|$)).+"
OUTPUT_CONTRACT_IDENTITY = {
    "schema_version": 1,
    "manifest_kind": "isonclust3-output-contract-register",
    "manifest_id": "isonclust3-final-clusters-contract-v1",
    "project": "isONclust3",
    "contract": "final_clusters.tsv",
}
OUTPUT_CONTRACT_SCHEMA_REQUIRED_FIELDS = {
    "$schema",
    "schema_version",
    "manifest_kind",
    "manifest_id",
    "project",
    "contract",
    "entries",
}
OUTPUT_CONTRACT_SCHEMA_ENTRY_FIELDS = {
    "entry_id",
    "mode",
    "benchmark_tier",
    "run_path",
    "fastq_path",
    "fastq_sha256",
    "fastq_bytes",
    "sha256",
    "bytes",
    "status",
    "consumer",
}


def sha256(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_output_contract_register(repo: Path) -> list[str]:
    path = repo / OUTPUT_CONTRACT_REGISTER
    errors: list[str] = []
    errors.extend(validate_output_contract_schema(repo))
    try:
        register = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"{path.relative_to(repo)} is invalid JSON: {exc}"]

    expected_root = {
        "$schema": OUTPUT_CONTRACT_SCHEMA_REFERENCE,
        **OUTPUT_CONTRACT_IDENTITY,
    }
    for key, value in expected_root.items():
        if register.get(key) != value:
            errors.append(f"{path.relative_to(repo)} {key} must be {value}")

    entries = register.get("entries")
    if not isinstance(entries, list):
        return errors + [f"{path.relative_to(repo)} entries must be a list"]

    observed_ids: set[str] = set()
    observed_order: list[str] = []
    for entry in entries:
        if not isinstance(entry, dict):
            errors.append(f"{path.relative_to(repo)} entry must be an object")
            continue
        entry_id = entry.get("entry_id")
        if not isinstance(entry_id, str):
            errors.append(f"{path.relative_to(repo)} entry_id must be a string")
            continue
        if entry_id in observed_ids:
            errors.append(f"{path.relative_to(repo)} duplicate entry_id: {entry_id}")
        observed_ids.add(entry_id)
        observed_order.append(entry_id)
        expected = REQUIRED_OUTPUT_CONTRACT_ENTRIES.get(entry_id)
        if expected is None:
            errors.append(f"{path.relative_to(repo)} unexpected entry_id: {entry_id}")
            continue
        for key, value in expected.items():
            if entry.get(key) != value:
                errors.append(f"{path.relative_to(repo)} {entry_id}.{key} must be {value}")
        if entry.get("benchmark_tier") != "toy":
            errors.append(f"{path.relative_to(repo)} {entry_id}.benchmark_tier must be toy")
        if entry.get("status") != "resolved":
            errors.append(f"{path.relative_to(repo)} {entry_id}.status must be resolved")
        if entry.get("consumer") != "newONform":
            errors.append(f"{path.relative_to(repo)} {entry_id}.consumer must be newONform")
        referenced_paths: dict[str, Path] = {}
        for path_field in ("run_path", "fastq_path"):
            value = entry.get(path_field)
            if not isinstance(value, str) or not value:
                errors.append(f"{path.relative_to(repo)} {entry_id}.{path_field} must be non-empty")
                continue
            relative_path = Path(value)
            if relative_path.is_absolute() or ".." in relative_path.parts:
                errors.append(
                    f"{path.relative_to(repo)} {entry_id}.{path_field} must be relative and non-escaping"
                )
                continue
            referenced_paths[path_field] = repo / relative_path
        run_path = referenced_paths.get("run_path")
        fastq_path = referenced_paths.get("fastq_path")
        for referenced_path in (run_path, fastq_path):
            if referenced_path is None:
                continue
            if not referenced_path.is_file():
                errors.append(
                    f"{path.relative_to(repo)} {entry_id} references missing file: "
                    f"{referenced_path.relative_to(repo)}"
                )
        expected_sha = entry.get("sha256")
        if not isinstance(expected_sha, str) or not SHA256_HEX_PATTERN.fullmatch(expected_sha):
            errors.append(f"{path.relative_to(repo)} {entry_id}.sha256 must be lowercase hex")
        elif run_path is not None and run_path.is_file() and sha256(run_path) != expected_sha:
            errors.append(f"{path.relative_to(repo)} {entry_id}.sha256 mismatch")
        expected_bytes = entry.get("bytes")
        if not isinstance(expected_bytes, int) or expected_bytes < 1:
            errors.append(f"{path.relative_to(repo)} {entry_id}.bytes must be positive")
        elif run_path is not None and run_path.is_file() and run_path.stat().st_size != expected_bytes:
            errors.append(f"{path.relative_to(repo)} {entry_id}.bytes mismatch")
        expected_fastq_sha = entry.get("fastq_sha256")
        if not isinstance(expected_fastq_sha, str) or not SHA256_HEX_PATTERN.fullmatch(
            expected_fastq_sha
        ):
            errors.append(
                f"{path.relative_to(repo)} {entry_id}.fastq_sha256 must be lowercase hex"
            )
        elif fastq_path is not None and fastq_path.is_file() and sha256(fastq_path) != expected_fastq_sha:
            errors.append(f"{path.relative_to(repo)} {entry_id}.fastq_sha256 mismatch")
        expected_fastq_bytes = entry.get("fastq_bytes")
        if not isinstance(expected_fastq_bytes, int) or expected_fastq_bytes < 1:
            errors.append(
                f"{path.relative_to(repo)} {entry_id}.fastq_bytes must be positive"
            )
        elif (
            fastq_path is not None
            and fastq_path.is_file()
            and fastq_path.stat().st_size != expected_fastq_bytes
        ):
            errors.append(f"{path.relative_to(repo)} {entry_id}.fastq_bytes mismatch")

    missing = set(REQUIRED_OUTPUT_CONTRACT_ENTRIES) - observed_ids
    if missing:
        errors.append(
            f"{path.relative_to(repo)} missing entry_id(s): {', '.join(sorted(missing))}"
        )
    if observed_order != list(REQUIRED_OUTPUT_CONTRACT_ENTRY_IDS):
        errors.append(
            f"{path.relative_to(repo)} entry order must be "
            f"{', '.join(REQUIRED_OUTPUT_CONTRACT_ENTRY_IDS)}"
        )
    return errors


def validate_output_contract_schema(repo: Path) -> list[str]:
    path = repo / OUTPUT_CONTRACT_SCHEMA
    errors: list[str] = []
    try:
        schema = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        return [f"{path.relative_to(repo)} is not readable: {exc}"]
    except json.JSONDecodeError as exc:
        return [f"{path.relative_to(repo)} is invalid JSON: {exc}"]

    expected_root = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://github.com/sagrudd/isONclust3/schemas/output-contract-register.schema.json",
        "type": "object",
        "additionalProperties": False,
    }
    for key, value in expected_root.items():
        if schema.get(key) != value:
            errors.append(f"{path.relative_to(repo)} {key} must be {value}")

    required = schema.get("required")
    if not isinstance(required, list) or set(required) != OUTPUT_CONTRACT_SCHEMA_REQUIRED_FIELDS:
        errors.append(f"{path.relative_to(repo)} required fields are incomplete")

    properties = schema.get("properties", {})
    if not isinstance(properties, dict):
        return errors + [f"{path.relative_to(repo)} properties must be an object"]
    expected_consts = {
        "$schema": OUTPUT_CONTRACT_SCHEMA_REFERENCE,
        **OUTPUT_CONTRACT_IDENTITY,
    }
    for field, value in expected_consts.items():
        if properties.get(field, {}).get("const") != value:
            errors.append(f"{path.relative_to(repo)} properties.{field}.const must be {value}")
    entries = properties.get("entries", {})
    if (
        entries.get("minItems") != len(REQUIRED_OUTPUT_CONTRACT_ENTRY_IDS)
        or entries.get("maxItems") != len(REQUIRED_OUTPUT_CONTRACT_ENTRY_IDS)
        or entries.get("items", {}).get("$ref") != "#/$defs/entry"
    ):
        errors.append(f"{path.relative_to(repo)} entries must require entry definitions")

    entry = schema.get("$defs", {}).get("entry", {})
    if not isinstance(entry, dict):
        return errors + [f"{path.relative_to(repo)} $defs.entry must be an object"]
    if entry.get("additionalProperties") is not False:
        errors.append(f"{path.relative_to(repo)} entry additionalProperties must be false")
    entry_required = entry.get("required")
    if not isinstance(entry_required, list) or set(entry_required) != OUTPUT_CONTRACT_SCHEMA_ENTRY_FIELDS:
        errors.append(f"{path.relative_to(repo)} entry required fields are incomplete")
    entry_properties = entry.get("properties", {})
    if not isinstance(entry_properties, dict):
        return errors + [f"{path.relative_to(repo)} entry properties must be an object"]
    if entry_properties.get("mode", {}).get("enum") != ["ont", "pacbio"]:
        errors.append(f"{path.relative_to(repo)} entry mode must be ont or pacbio")
    if entry_properties.get("benchmark_tier", {}).get("const") != "toy":
        errors.append(f"{path.relative_to(repo)} entry benchmark_tier must be toy")
    for path_field in ("run_path", "fastq_path"):
        if entry_properties.get(path_field, {}).get("pattern") != OUTPUT_CONTRACT_RELATIVE_PATH_PATTERN:
            errors.append(
                f"{path.relative_to(repo)} {path_field} must require relative non-escaping paths"
            )
    if entry_properties.get("status", {}).get("const") != "resolved":
        errors.append(f"{path.relative_to(repo)} entry status must be resolved")
    if entry_properties.get("consumer", {}).get("const") != "newONform":
        errors.append(f"{path.relative_to(repo)} entry consumer must be newONform")
    for checksum_field in ("sha256", "fastq_sha256"):
        if entry_properties.get(checksum_field, {}).get("pattern") != "^[0-9a-f]{64}$":
            errors.append(f"{path.relative_to(repo)} {checksum_field} must gate sha256 hex")
    for byte_field in ("bytes", "fastq_bytes"):
        if entry_properties.get(byte_field, {}).get("minimum") != 1:
            errors.append(f"{path.relative_to(repo)} {byte_field} must be positive")
    return errors
