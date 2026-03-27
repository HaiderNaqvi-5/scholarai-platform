#!/usr/bin/env python3
"""ScholarAI docs governance checks.

Checks:
1) Terminology gate: blocks MVP/Post-MVP wording in README/docs markdown.
2) Local-link integrity gate: verifies local markdown links resolve.
3) Canonical-tail gate: ensures canonical docs include required tail sections.

Exit code is non-zero when any enabled check fails.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple


REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_ROOT = REPO_ROOT / "docs"
ROOT_README = REPO_ROOT / "README.md"

GITHUB_ANNOTATION = "::error file={file},line={line},title={title}::{message}"

TERMINOLOGY_PATTERNS = [
    re.compile(r"\bMVP\b"),
    re.compile(r"Post-MVP", re.IGNORECASE),
]

CANONICAL_DOCS = [
    DOCS_ROOT / "PRD.md",
    DOCS_ROOT / "scholarai" / "01_executive_summary.md",
    DOCS_ROOT / "scholarai" / "02_prd_and_scope.md",
    DOCS_ROOT / "scholarai" / "04_requirements_and_governance.md",
]

REQUIRED_CANONICAL_TAIL_SECTIONS = [
    "## SLC decision (v0.1)",
    "## Deferred By Stage",
    "## Assumptions",
    "## Risks",
]


def relpath(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT)).replace("\\", "/")


def markdown_files() -> List[Path]:
    files = [ROOT_README] if ROOT_README.exists() else []
    files.extend(sorted(DOCS_ROOT.rglob("*.md")))
    return files


def find_terminology_failures(paths: Sequence[Path]) -> List[Tuple[Path, int, str]]:
    failures: List[Tuple[Path, int, str]] = []
    for path in paths:
        content = path.read_text(encoding="utf-8", errors="replace").splitlines()
        for idx, line in enumerate(content, start=1):
            for pattern in TERMINOLOGY_PATTERNS:
                if pattern.search(line):
                    failures.append((path, idx, line.strip()))
                    break
    return failures


LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def iter_local_links(path: Path, content: str) -> Iterable[Tuple[int, str]]:
    for idx, line in enumerate(content.splitlines(), start=1):
        for m in LINK_RE.finditer(line):
            link = m.group(1).strip()
            if not link:
                continue
            if link.startswith(("http://", "https://", "mailto:", "#")):
                continue
            yield idx, link


def resolve_link(current_file: Path, raw_link: str) -> Path:
    link = raw_link.split("#", 1)[0].split("?", 1)[0].strip()
    if re.match(r"^[A-Za-z]:[/\\]", link):
        # Normalize Windows-style absolute path
        return Path(link)
    if link.startswith("/"):
        return REPO_ROOT / link.lstrip("/")
    return (current_file.parent / link).resolve()


def find_broken_local_links(paths: Sequence[Path]) -> List[Tuple[Path, int, str]]:
    failures: List[Tuple[Path, int, str]] = []
    for path in paths:
        content = path.read_text(encoding="utf-8", errors="replace")
        for line_no, raw_link in iter_local_links(path, content):
            target = resolve_link(path, raw_link)
            if not target.exists():
                failures.append((path, line_no, raw_link))
    return failures


def find_canonical_tail_failures(paths: Sequence[Path]) -> List[Tuple[Path, str]]:
    failures: List[Tuple[Path, str]] = []
    for path in paths:
        if not path.exists():
            failures.append((path, "Missing canonical file"))
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for required in REQUIRED_CANONICAL_TAIL_SECTIONS:
            if required not in text:
                failures.append((path, f"Missing section: {required}"))
    return failures


def print_error(file_path: Path, line: int, title: str, message: str) -> None:
    print(
        GITHUB_ANNOTATION.format(
            file=relpath(file_path),
            line=line,
            title=title,
            message=message.replace("%", "%25").replace("\n", "%0A"),
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run ScholarAI docs governance checks.")
    parser.add_argument(
        "--skip-canonical-tail",
        action="store_true",
        help="Skip canonical-tail section checks.",
    )
    args = parser.parse_args()

    files = markdown_files()
    failures = 0

    terminology = find_terminology_failures(files)
    if terminology:
        failures += len(terminology)
        for path, line_no, line in terminology:
            print_error(path, line_no, "Terminology Gate", f"Blocked terminology: {line}")

    broken_links = find_broken_local_links(files)
    if broken_links:
        failures += len(broken_links)
        for path, line_no, raw_link in broken_links:
            print_error(path, line_no, "Link Integrity", f"Broken local link: {raw_link}")

    canonical_failures: List[Tuple[Path, str]] = []
    if not args.skip_canonical_tail:
        canonical_failures = find_canonical_tail_failures(CANONICAL_DOCS)
        failures += len(canonical_failures)
        for path, issue in canonical_failures:
            print_error(path, 1, "Canonical Tail Gate", issue)

    summary_lines = [
        "Docs governance summary:",
        f"- terminology failures: {len(terminology)}",
        f"- broken links: {len(broken_links)}",
        f"- canonical-tail failures: {len(canonical_failures)}",
        f"- total failures: {failures}",
    ]
    print("\n".join(summary_lines))

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
