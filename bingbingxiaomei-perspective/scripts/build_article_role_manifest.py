#!/usr/bin/env python3
"""Build a role-aware segment manifest without modifying source articles."""

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARTICLES_DIR = PROJECT_ROOT / "references" / "sources" / "articles"
DEFAULT_OVERRIDES_PATH = (
    PROJECT_ROOT
    / "references"
    / "research"
    / "article-content-role-overrides.json"
)
DEFAULT_OUTPUT_PATH = (
    PROJECT_ROOT
    / "references"
    / "research"
    / "article-content-roles.jsonl"
)
VALID_ROLES = {
    "author_post",
    "author_reply",
    "third_party_comment",
    "secondary_analysis",
    "unknown",
}
ROLE_ELIGIBILITY = {
    "author_post": "author_primary",
    "author_reply": "author_primary",
    "third_party_comment": "context_only",
    "secondary_analysis": "excluded",
    "unknown": "excluded",
}
COMMENT_HEADER_RE = re.compile(
    r"^(?:>\s*)*\[([^\]]+)\]\(https://xueqiu\.com/(\d+)\)(.*)$"
)
ARTICLE_URL_RE = re.compile(r"https://xueqiu\.com/(\d+)/")
FRONTMATTER_AUTHOR_RE = re.compile(r'-\s+"\[\[([^\]]+)\]\]"')


def sha256_text(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def parse_frontmatter(lines, article_path):
    author_name = None
    author_uid = None
    frontmatter_end = 0

    if lines and lines[0].strip() == "---":
        for index in range(1, len(lines)):
            if lines[index].strip() == "---":
                frontmatter_end = index + 1
                break
            author_match = FRONTMATTER_AUTHOR_RE.search(lines[index])
            if author_match:
                author_name = author_match.group(1)
            url_match = ARTICLE_URL_RE.search(lines[index])
            if url_match:
                author_uid = url_match.group(1)

    if author_name is None:
        filename_parts = article_path.name.split("_", 2)
        if len(filename_parts) >= 2:
            author_name = filename_parts[1]

    return {
        "author_name": author_name,
        "author_uid": author_uid,
        "frontmatter_end": frontmatter_end,
    }


def is_meaningful(line):
    stripped = line.strip()
    return bool(stripped and set(stripped) != {"-"})


def find_body_start(lines, frontmatter_end):
    for index in range(frontmatter_end, len(lines)):
        if lines[index].startswith("来自 ["):
            for body_index in range(index + 1, len(lines)):
                if is_meaningful(lines[body_index]):
                    return body_index

    for index in range(frontmatter_end, len(lines)):
        stripped = lines[index].strip()
        if not stripped or stripped.startswith("#"):
            continue
        return index
    return len(lines)


def trim_range(lines, start_index, end_index):
    while start_index <= end_index and not is_meaningful(lines[start_index]):
        start_index += 1
    while end_index >= start_index and not is_meaningful(lines[end_index]):
        end_index -= 1
    if start_index > end_index:
        return None
    return start_index, end_index


def make_segment(
    lines,
    article_path,
    start_index,
    end_index,
    role,
    speaker_name,
    speaker_uid,
    classification_source="rule",
):
    text = "\n".join(lines[start_index : end_index + 1])
    text_digest = sha256_text(text)
    start_line = start_index + 1
    end_line = end_index + 1
    segment_key = (
        f"{article_path}:{start_line}:{end_line}:{text_digest}"
    )
    return {
        "article_path": article_path,
        "segment_id": sha256_text(segment_key),
        "start_line": start_line,
        "end_line": end_line,
        "role": role,
        "speaker_name": speaker_name,
        "speaker_uid": speaker_uid,
        "evidence_eligibility": ROLE_ELIGIBILITY[role],
        "classification_source": classification_source,
        "text_digest": text_digest,
    }


def build_rule_segments(lines, article_path, metadata):
    body_start = find_body_start(lines, metadata["frontmatter_end"])
    if body_start >= len(lines):
        return []

    segments = []
    current_start = body_start
    current_role = "author_post"
    current_name = metadata["author_name"]
    current_uid = metadata["author_uid"]

    for index in range(body_start, len(lines)):
        header_match = COMMENT_HEADER_RE.match(lines[index])
        if not header_match:
            continue

        trimmed = trim_range(lines, current_start, index - 1)
        if trimmed:
            segments.append(
                make_segment(
                    lines,
                    article_path,
                    *trimmed,
                    current_role,
                    current_name,
                    current_uid,
                )
            )

        speaker_name, speaker_uid = header_match.group(1), header_match.group(2)
        current_start = index
        current_name = speaker_name
        current_uid = speaker_uid
        current_role = (
            "author_reply"
            if metadata["author_uid"] and speaker_uid == metadata["author_uid"]
            else "third_party_comment"
        )

    trimmed = trim_range(lines, current_start, len(lines) - 1)
    if trimmed:
        segments.append(
            make_segment(
                lines,
                article_path,
                *trimmed,
                current_role,
                current_name,
                current_uid,
            )
        )
    return segments


def apply_override(lines, segment, override):
    start_line = int(override["start_line"])
    end_line = int(override["end_line"])
    role = override["role"]
    reason = str(override.get("reason", "")).strip()
    if role not in VALID_ROLES:
        raise ValueError(f"invalid override role: {role}")
    if not reason:
        raise ValueError("override reason is required")
    if not (
        segment["start_line"] <= start_line
        and end_line <= segment["end_line"]
        and start_line <= end_line
    ):
        return [segment], False

    pieces = []
    inherited = {
        "speaker_name": segment["speaker_name"],
        "speaker_uid": segment["speaker_uid"],
    }
    if segment["start_line"] < start_line:
        pieces.append(
            make_segment(
                lines,
                segment["article_path"],
                segment["start_line"] - 1,
                start_line - 2,
                segment["role"],
                **inherited,
            )
        )
    pieces.append(
        make_segment(
            lines,
            segment["article_path"],
            start_line - 1,
            end_line - 1,
            role,
            classification_source="reviewed_override",
            **inherited,
        )
    )
    if end_line < segment["end_line"]:
        pieces.append(
            make_segment(
                lines,
                segment["article_path"],
                end_line,
                segment["end_line"] - 1,
                segment["role"],
                **inherited,
            )
        )
    return pieces, True


def apply_overrides(lines, article_path, segments, overrides):
    applicable = [
        override
        for override in overrides
        if override.get("article_path") == article_path
    ]
    for override in applicable:
        updated = []
        applied = False
        for segment in segments:
            pieces, matched = apply_override(lines, segment, override)
            updated.extend(pieces)
            applied = applied or matched
        if not applied:
            raise ValueError(
                "override does not fit one segment: "
                f"{article_path}:{override.get('start_line')}-"
                f"{override.get('end_line')}"
            )
        segments = updated
    return sorted(segments, key=lambda item: item["start_line"])


def validate_segments(segments):
    for segment in segments:
        if segment["role"] not in VALID_ROLES:
            raise ValueError(f"invalid role: {segment['role']}")
        if (
            segment["evidence_eligibility"] == "author_primary"
            and segment["role"] not in {"author_post", "author_reply"}
        ):
            raise ValueError("non-author segment cannot be primary evidence")

    for previous, current in zip(segments, segments[1:]):
        if previous["end_line"] >= current["start_line"]:
            raise ValueError(
                f"overlapping segments in {current['article_path']}"
            )


def parse_article(article_path, relative_path, overrides=None):
    lines = article_path.read_text(encoding="utf-8").splitlines()
    metadata = parse_frontmatter(lines, article_path)
    segments = build_rule_segments(lines, relative_path, metadata)
    segments = apply_overrides(
        lines,
        relative_path,
        segments,
        overrides or [],
    )
    validate_segments(segments)
    return segments


def load_overrides(path):
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ValueError("unsupported override schema_version")
    overrides = data.get("overrides")
    if not isinstance(overrides, list):
        raise ValueError("overrides must be a list")
    return overrides


def build_manifest(articles_dir, overrides):
    manifest = []
    project_root = articles_dir.parents[2]
    for article_path in sorted(articles_dir.glob("*.md")):
        relative_path = article_path.relative_to(project_root).as_posix()
        manifest.extend(
            parse_article(article_path, relative_path, overrides)
        )
    return manifest


def manifest_stats(manifest):
    role_counts = Counter(item["role"] for item in manifest)
    eligibility_counts = Counter(
        item["evidence_eligibility"] for item in manifest
    )
    article_paths = {item["article_path"] for item in manifest}
    non_author = [
        item
        for item in manifest
        if item["role"] in {"third_party_comment", "secondary_analysis"}
    ]
    return {
        "article_count": len(article_paths),
        "segment_count": len(manifest),
        "role_counts": dict(sorted(role_counts.items())),
        "eligibility_counts": dict(sorted(eligibility_counts.items())),
        "non_author_file_count": len(
            {item["article_path"] for item in non_author}
        ),
        "non_author_segment_count": len(non_author),
        "distinct_non_author_uid_count": len(
            {
                item["speaker_uid"]
                for item in non_author
                if item["speaker_uid"]
            }
        ),
        "unknown_segment_count": role_counts.get("unknown", 0),
    }


def write_jsonl(path, manifest):
    path.parent.mkdir(parents=True, exist_ok=True)
    content = "".join(
        json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n"
        for item in manifest
    )
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(content, encoding="utf-8", newline="\n")
    temp_path.replace(path)


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--articles-dir",
        type=Path,
        default=DEFAULT_ARTICLES_DIR,
    )
    parser.add_argument(
        "--overrides",
        type=Path,
        default=DEFAULT_OVERRIDES_PATH,
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    overrides = load_overrides(args.overrides)
    manifest = build_manifest(args.articles_dir, overrides)
    write_jsonl(args.output, manifest)
    print(json.dumps(manifest_stats(manifest), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
