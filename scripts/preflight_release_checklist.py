"""Release checklist checks for isONclust3 release preflight."""

from __future__ import annotations

import re
from pathlib import Path

REQUIRED_RELEASE_CHECKLIST_SECTIONS = (
    "## Required Local Checks",
    "## Required Docker And GB10 Evidence",
    "## Required Integration Evidence",
)


def validate_release_checklist(repo: Path, active_blockers: set[str]) -> list[str]:
    path = repo / "RELEASE_CHECKLIST.md"
    text = path.read_text(encoding="utf-8")
    errors = [
        f"RELEASE_CHECKLIST.md missing section: {section}"
        for section in REQUIRED_RELEASE_CHECKLIST_SECTIONS
        if section not in text
    ]
    for blocker in sorted(active_blockers):
        if blocker not in text:
            errors.append(f"RELEASE_CHECKLIST.md missing blocker marker: {blocker}")
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
