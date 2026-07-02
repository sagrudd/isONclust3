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
SHA256_HEX_PATTERN = re.compile(r"[0-9a-f]{64}")


def sha256(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_output_contract_register(repo: Path) -> list[str]:
    path = repo / "fixtures" / "output-contracts" / "final-clusters-register.json"
    errors: list[str] = []
    try:
        register = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"{path.relative_to(repo)} is invalid JSON: {exc}"]

    expected_root = {
        "schema_version": 1,
        "manifest_kind": "isonclust3-output-contract-register",
        "manifest_id": "isonclust3-final-clusters-contract-v1",
        "project": "isONclust3",
        "contract": "final_clusters.tsv",
    }
    for key, value in expected_root.items():
        if register.get(key) != value:
            errors.append(f"{path.relative_to(repo)} {key} must be {value}")

    entries = register.get("entries")
    if not isinstance(entries, list):
        return errors + [f"{path.relative_to(repo)} entries must be a list"]

    observed_ids: set[str] = set()
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
        run_path = repo / str(entry.get("run_path", ""))
        fastq_path = repo / str(entry.get("fastq_path", ""))
        for referenced_path in (run_path, fastq_path):
            if not referenced_path.is_file():
                errors.append(
                    f"{path.relative_to(repo)} {entry_id} references missing file: "
                    f"{referenced_path.relative_to(repo)}"
                )
        expected_sha = entry.get("sha256")
        if not isinstance(expected_sha, str) or not SHA256_HEX_PATTERN.fullmatch(expected_sha):
            errors.append(f"{path.relative_to(repo)} {entry_id}.sha256 must be lowercase hex")
        elif run_path.is_file() and sha256(run_path) != expected_sha:
            errors.append(f"{path.relative_to(repo)} {entry_id}.sha256 mismatch")
        expected_bytes = entry.get("bytes")
        if not isinstance(expected_bytes, int) or expected_bytes < 1:
            errors.append(f"{path.relative_to(repo)} {entry_id}.bytes must be positive")
        elif run_path.is_file() and run_path.stat().st_size != expected_bytes:
            errors.append(f"{path.relative_to(repo)} {entry_id}.bytes mismatch")
        expected_fastq_sha = entry.get("fastq_sha256")
        if not isinstance(expected_fastq_sha, str) or not SHA256_HEX_PATTERN.fullmatch(
            expected_fastq_sha
        ):
            errors.append(
                f"{path.relative_to(repo)} {entry_id}.fastq_sha256 must be lowercase hex"
            )
        elif fastq_path.is_file() and sha256(fastq_path) != expected_fastq_sha:
            errors.append(f"{path.relative_to(repo)} {entry_id}.fastq_sha256 mismatch")
        expected_fastq_bytes = entry.get("fastq_bytes")
        if not isinstance(expected_fastq_bytes, int) or expected_fastq_bytes < 1:
            errors.append(
                f"{path.relative_to(repo)} {entry_id}.fastq_bytes must be positive"
            )
        elif fastq_path.is_file() and fastq_path.stat().st_size != expected_fastq_bytes:
            errors.append(f"{path.relative_to(repo)} {entry_id}.fastq_bytes mismatch")

    missing = set(REQUIRED_OUTPUT_CONTRACT_ENTRIES) - observed_ids
    if missing:
        errors.append(
            f"{path.relative_to(repo)} missing entry_id(s): {', '.join(sorted(missing))}"
        )
    return errors
