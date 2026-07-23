#!/usr/bin/env python3
"""Audit G1 Phase 2 evidence against the G1a author-primary view."""

import argparse
import json
import re
import unicodedata
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = (
    PROJECT_ROOT / "references" / "research" / "article-content-roles.jsonl"
)
DEFAULT_CANDIDATES = (
    PROJECT_ROOT
    / "references"
    / "research"
    / "g1-local"
    / "phase-2-candidates.md"
)
DEFAULT_OUTPUT = (
    PROJECT_ROOT
    / "references"
    / "research"
    / "g1-local"
    / "g1a-author-primary-audit.json"
)
AUDITED_SOURCE_FILES = (
    "01-writings.md",
    "02-conversations.md",
    "03-expression-dna.md",
    "05-decisions.md",
    "06-timeline.md",
    "phase-2-candidates.md",
)
AUTHOR_PRIMARY_REQUIRED_FILES = {
    "01-writings.md",
    "03-expression-dna.md",
    "05-decisions.md",
    "06-timeline.md",
    "phase-2-candidates.md",
}

REFERENCE_RE = re.compile(
    r"`([^`]+\.md)`(?:：“|，摘录：“)([^”]+)”"
)
MODEL_HEADING_RE = re.compile(r"^###\s+(M\d+)\.")
HEURISTIC_HEADING_RE = re.compile(r"^###\s+(H\d+)\.")
MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]+\)")
PUNCTUATION_RE = re.compile(
    r"[\s，。、“”‘’：；！？…·—→（）()\[\]《》,.!?;:'\"+-]+"
)
QUOTE_PART_RE = re.compile(r"[\s，。、“”‘’：；！？…·—→（）()\[\]《》,.!?;:'\"+-]+")


def normalize_text(text):
    text = unicodedata.normalize("NFKC", text)
    text = MARKDOWN_LINK_RE.sub(r"\1", text)
    return PUNCTUATION_RE.sub("", text)


def quote_parts(quote):
    return [
        normalize_text(part)
        for part in QUOTE_PART_RE.split(quote)
        if len(normalize_text(part)) >= 2
    ]


def match_quote(quote, source_text):
    normalized_quote = normalize_text(quote)
    normalized_source = normalize_text(source_text)
    if normalized_quote and normalized_quote in normalized_source:
        return "exact"
    parts = quote_parts(quote)
    if parts and all(part in normalized_source for part in parts):
        return "paraphrase_supported"
    return "not_found"


def normalize_path_key(path):
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", Path(path).name))


def load_manifest(path):
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def resolve_article_path(project_root, cited_path, article_paths):
    direct = project_root / "references" / "sources" / "articles" / cited_path
    if direct.exists():
        return direct
    cited_key = normalize_path_key(cited_path)
    matches = [
        path for path in article_paths if normalize_path_key(path) == cited_key
    ]
    if len(matches) == 1:
        return matches[0]
    return None


def extract_references(candidate_text, source_file):
    section = None
    candidate_id = None
    references = []
    for line_number, line in enumerate(candidate_text.splitlines(), start=1):
        if line == "## 候选模型":
            section = "candidate_model"
            candidate_id = None
        elif line == "## 候选启发式":
            section = "candidate_heuristic"
            candidate_id = None
        elif line.startswith("## "):
            section = "supporting_analysis"
            candidate_id = None

        model_match = MODEL_HEADING_RE.match(line)
        heuristic_match = HEURISTIC_HEADING_RE.match(line)
        if model_match:
            candidate_id = model_match.group(1)
        elif heuristic_match:
            candidate_id = heuristic_match.group(1)

        for cited_path, quote in REFERENCE_RE.findall(line):
            references.append(
                {
                    "author_primary_required": (
                        source_file in AUTHOR_PRIMARY_REQUIRED_FILES
                    ),
                    "candidate_id": candidate_id,
                    "section": section,
                    "source_file": source_file,
                    "source_line": line_number,
                    "cited_path": cited_path,
                    "quote": quote,
                }
            )
    return references


def build_audit_report(project_root=PROJECT_ROOT):
    project_root = Path(project_root)
    manifest_path = (
        project_root
        / "references"
        / "research"
        / "article-content-roles.jsonl"
    )
    candidate_path = (
        project_root
        / "references"
        / "research"
        / "g1-local"
        / "phase-2-candidates.md"
    )
    manifest = load_manifest(manifest_path)
    source_paths = [
        candidate_path.parent / source_file
        for source_file in AUDITED_SOURCE_FILES
    ]
    references = []
    for source_path in source_paths:
        references.extend(
            extract_references(
                source_path.read_text(encoding="utf-8"),
                source_path.name,
            )
        )
    article_paths = sorted(
        (project_root / "references" / "sources" / "articles").glob("*.md")
    )

    segments_by_path = {}
    for segment in manifest:
        segments_by_path.setdefault(segment["article_path"], []).append(segment)

    audited = []
    for reference in references:
        article_path = resolve_article_path(
            project_root,
            reference["cited_path"],
            article_paths,
        )
        result = dict(reference)
        if article_path is None:
            result["status"] = "missing_article"
            result["resolved_article_path"] = None
            result["matched_segment_id"] = None
            audited.append(result)
            continue

        relative_path = article_path.relative_to(project_root).as_posix()
        lines = article_path.read_text(encoding="utf-8").splitlines()
        primary_segments = [
            segment
            for segment in segments_by_path.get(relative_path, [])
            if segment["evidence_eligibility"] == "author_primary"
        ]
        all_segments = segments_by_path.get(relative_path, [])

        status = "not_found"
        matched_segment_id = None
        for segment in primary_segments:
            source_text = "\n".join(
                lines[segment["start_line"] - 1 : segment["end_line"]]
            )
            candidate_status = match_quote(reference["quote"], source_text)
            if candidate_status != "not_found":
                status = candidate_status
                matched_segment_id = segment["segment_id"]
                break

        if status == "not_found":
            for segment in all_segments:
                source_text = "\n".join(
                    lines[segment["start_line"] - 1 : segment["end_line"]]
                )
                if match_quote(reference["quote"], source_text) != "not_found":
                    status = "non_author"
                    matched_segment_id = segment["segment_id"]
                    break

        result["status"] = status
        result["resolved_article_path"] = relative_path
        result["matched_segment_id"] = matched_segment_id
        audited.append(result)

    unresolved_statuses = {"missing_article", "not_found"}
    candidate_models = {
        item["candidate_id"]
        for item in audited
        if item["section"] == "candidate_model" and item["candidate_id"]
    }
    candidate_heuristics = {
        item["candidate_id"]
        for item in audited
        if item["section"] == "candidate_heuristic" and item["candidate_id"]
    }
    status_counts = {}
    for item in audited:
        status_counts[item["status"]] = status_counts.get(item["status"], 0) + 1

    return {
        "schema_version": 1,
        "gate": "G1a",
        "source_candidate_file": candidate_path.relative_to(
            project_root
        ).as_posix(),
        "audited_source_files": [
            path.relative_to(project_root).as_posix()
            for path in source_paths
        ],
        "audited_source_file_count": len(source_paths),
        "role_manifest": manifest_path.relative_to(project_root).as_posix(),
        "evidence_reference_count": len(audited),
        "status_counts": dict(sorted(status_counts.items())),
        "unresolved_reference_count": sum(
            item["status"] in unresolved_statuses for item in audited
        ),
        "non_author_reference_count": sum(
            item["status"] == "non_author"
            and item["author_primary_required"]
            for item in audited
        ),
        "contextual_non_author_reference_count": sum(
            item["status"] == "non_author"
            and not item["author_primary_required"]
            for item in audited
        ),
        "candidate_model_count": len(candidate_models),
        "candidate_heuristic_count": len(candidate_heuristics),
        "references": audited,
    }


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    report = build_audit_report(PROJECT_ROOT)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        json.dumps(
            {
                key: value
                for key, value in report.items()
                if key != "references"
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
