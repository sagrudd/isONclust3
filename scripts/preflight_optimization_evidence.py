"""Optimization evidence checks for isONclust3 release preflight."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

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
