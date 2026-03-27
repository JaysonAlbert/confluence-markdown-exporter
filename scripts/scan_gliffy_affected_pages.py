#!/usr/bin/env python3
"""Scan an exported Confluence tree for pages affected by missing Gliffy handling."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote


REMOTE_GLIFIY_IMAGE_RE = re.compile(r"/download/attachments/\d+/[^)\s]+\.png(?:\?[^)\s]*)?")
LOCAL_GLIFFY_LINK_RE = re.compile(r"\.gliffy\.(?:png|json)\b")
LOCAL_GLIFFY_PREVIEW_RE = re.compile(r"\[!\[[^\]]*\]\(([^)]+\.png)\)\]\(([^)]+\.gliffy\.json)\)")


@dataclass
class PageFinding:
    page_id: str
    title: str
    markdown_path: str
    attachment_dir: str
    gliffy_json_count: int
    gliffy_png_count: int
    remote_gliffy_links: list[str]
    reasons: list[str]


def load_lockfile(lockfile_path: Path) -> dict[str, dict[str, str]]:
    lock_data = json.loads(lockfile_path.read_text())
    pages = lock_data.get("pages", {})
    return {str(page_id): entry for page_id, entry in pages.items()}


def extract_page_id(markdown_path: Path) -> str | None:
    match = re.search(r"-(\d+)\.md$", markdown_path.name)
    return match.group(1) if match else None


def scan_page(markdown_path: Path, lock_pages: dict[str, dict[str, str]]) -> PageFinding | None:
    page_id = extract_page_id(markdown_path)
    if page_id is None:
        return None

    title = markdown_path.stem.rsplit("-", 1)[0]
    attachment_dir = markdown_path.parent / title
    if not attachment_dir.exists():
        attachment_dir = markdown_path.parent / markdown_path.stem
    markdown_text = markdown_path.read_text(errors="ignore")

    gliffy_json_files = sorted(attachment_dir.glob("*.gliffy.json")) if attachment_dir.exists() else []
    local_gliffy_link_count = len(LOCAL_GLIFFY_LINK_RE.findall(markdown_text))
    local_gliffy_preview_files = {
        (markdown_path.parent / unquote(image_path)).resolve()
        for image_path, _ in LOCAL_GLIFFY_PREVIEW_RE.findall(markdown_text)
    }
    existing_local_gliffy_preview_files = {
        path for path in local_gliffy_preview_files if path.exists()
    }

    remote_links = sorted(
        {
            link
            for link in REMOTE_GLIFIY_IMAGE_RE.findall(markdown_text)
            if page_id in link
        }
    )

    reasons: list[str] = []
    if gliffy_json_files and len(existing_local_gliffy_preview_files) < len(gliffy_json_files):
        reasons.append("missing_exported_gliffy_preview_png")
    if gliffy_json_files and local_gliffy_link_count < len(gliffy_json_files):
        reasons.append("gliffy_attachments_not_fully_referenced_in_markdown")
    if remote_links and not gliffy_json_files and local_gliffy_link_count == 0:
        reasons.append("markdown_still_uses_remote_gliffy_png")

    if not reasons:
        return None

    lock_entry = lock_pages.get(page_id, {})
    return PageFinding(
        page_id=page_id,
        title=lock_entry.get("title", title),
        markdown_path=str(markdown_path),
        attachment_dir=str(attachment_dir),
        gliffy_json_count=len(gliffy_json_files),
        gliffy_png_count=len(existing_local_gliffy_preview_files),
        remote_gliffy_links=remote_links,
        reasons=reasons,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "export_root",
        type=Path,
        help="Root directory of exported Confluence markdown tree",
    )
    parser.add_argument(
        "--lockfile",
        type=Path,
        default=None,
        help="Path to confluence-lock.json. Defaults to <export_root>/confluence-lock.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional path to write JSON results",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    export_root = args.export_root.resolve()
    lockfile_path = args.lockfile.resolve() if args.lockfile else export_root / "confluence-lock.json"

    if not export_root.exists():
        parser.error(f"export_root does not exist: {export_root}")
    if not lockfile_path.exists():
        parser.error(f"lockfile does not exist: {lockfile_path}")

    lock_pages = load_lockfile(lockfile_path)
    findings = [
        finding
        for markdown_path in sorted(export_root.rglob("*.md"))
        if (finding := scan_page(markdown_path, lock_pages)) is not None
    ]

    payload = {
        "export_root": str(export_root),
        "lockfile": str(lockfile_path),
        "affected_page_count": len(findings),
        "pages": [asdict(finding) for finding in findings],
    }

    rendered = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(rendered)
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
