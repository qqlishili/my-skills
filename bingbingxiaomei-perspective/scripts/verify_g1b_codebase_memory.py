#!/usr/bin/env python3
"""Verify the G1b codebase-memory author-primary text retrieval gate."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


QUERIES = [
    {
        "year": 2023,
        "phrase": "黄金细分可能非常复杂",
        "expected_prefix": "2023-03-10 161631_",
    },
    {
        "year": 2023,
        "phrase": "找到三者同时有利的节点",
        "expected_prefix": "2023-10-18 072901_",
    },
    {
        "year": 2024,
        "phrase": "6万亿 ， 2024-2026一致性置换地方隐性债务",
        "expected_prefix": "2024-11-08 183336_",
    },
    {
        "year": 2025,
        "phrase": "基于原始信息的分析 ， 则为次级信息",
        "expected_prefix": "2025-08-16 151943_",
    },
    {
        "year": 2026,
        "phrase": "信心我买的那一天就有了",
        "expected_prefix": "2026-05-21 224111_",
    },
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_roles(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def find_author_primary_match(
    root: Path, roles: list[dict], phrase: str
) -> tuple[Path, int, dict]:
    article_dir = root / "references" / "sources" / "articles"
    matches: list[tuple[Path, int, dict]] = []

    roles_by_path: dict[str, list[dict]] = {}
    for role in roles:
        roles_by_path.setdefault(role["article_path"], []).append(role)

    for path in article_dir.glob("*.md"):
        relative = path.relative_to(root).as_posix()
        lines = path.read_text(encoding="utf-8").splitlines()
        for line_number, line in enumerate(lines, 1):
            if phrase not in line:
                continue
            for role in roles_by_path.get(relative, []):
                if (
                    role["evidence_eligibility"] == "author_primary"
                    and role["start_line"] <= line_number <= role["end_line"]
                ):
                    matches.append((path, line_number, role))

    if len(matches) != 1:
        raise RuntimeError(
            f"expected one author_primary match for {phrase!r}, got {len(matches)}"
        )
    return matches[0]


def run_cli(executable: Path, shim_dir: Path, arguments: list[str]) -> dict:
    environment = os.environ.copy()
    environment["PATH"] = f"{shim_dir}{os.pathsep}{environment.get('PATH', '')}"
    command = [str(executable), "cli", *arguments]
    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=environment,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"codebase-memory failed for {arguments!r}: {completed.stderr.strip()}"
        )
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"codebase-memory returned invalid JSON for {arguments!r}"
        ) from exc


def run_search(
    executable: Path,
    shim_dir: Path,
    phrase: str,
    project: str,
    path_filter: str,
) -> dict:
    return run_cli(
        executable,
        shim_dir,
        [
            "search_code",
            "--pattern",
            phrase,
            "--project",
            project,
            "--path-filter",
            path_filter,
            "--mode",
            "full",
            "--limit",
            "5",
        ],
    )


def verify_result(result: dict, expected_prefix: str) -> dict:
    if result.get("total_results") != 1:
        raise RuntimeError(
            f"expected one indexed result, got {result.get('total_results')}"
        )
    if result.get("raw_match_count") != 0:
        raise RuntimeError("expected an indexed graph result, not a raw fallback")

    returned = result["results"][0]
    returned_file = returned.get("file", "")
    returned_name = returned_file.replace("\\", "/").rsplit("/", 1)[-1]
    if not returned_name.startswith(expected_prefix):
        raise RuntimeError(
            f"returned file {returned_file!r} does not start with {expected_prefix!r}"
        )
    return returned


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    parser.add_argument(
        "--executable",
        type=Path,
        default=Path.home() / ".local" / "bin" / "codebase-memory-mcp.exe",
    )
    parser.add_argument("--project", default="bingbingxiaomei-perspective-full")
    parser.add_argument(
        "--path-filter", default=r"^references/sources/articles/"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "references/research/g1-local/g1b-codebase-memory-receipt.json"
        ),
    )
    args = parser.parse_args()

    root = args.root.resolve()
    output = args.output if args.output.is_absolute() else root / args.output
    role_manifest = root / "references" / "research" / "article-content-roles.jsonl"
    shim = root / "scripts" / "tool-shims"
    roles = load_roles(role_manifest)
    records = []

    for query in QUERIES:
        path, line_number, role = find_author_primary_match(
            root, roles, query["phrase"]
        )
        if not path.name.startswith(query["expected_prefix"]):
            raise RuntimeError(
                f"local path {path.name!r} does not start with "
                f"{query['expected_prefix']!r}"
            )

        result = run_search(
            args.executable,
            shim,
            query["phrase"],
            args.project,
            args.path_filter,
        )
        returned = verify_result(result, query["expected_prefix"])
        records.append(
            {
                "year": query["year"],
                "query_phrase": query["phrase"],
                "expected_path": path.relative_to(root).as_posix(),
                "actual_path": path.relative_to(root).as_posix(),
                "segment_id": role["segment_id"],
                "expected_role": "author_primary",
                "actual_role": role["evidence_eligibility"],
                "source_role": role["role"],
                "line_number": line_number,
                "codebase_memory": {
                    "total_grep_matches": result["total_grep_matches"],
                    "total_results": result["total_results"],
                    "raw_match_count": result["raw_match_count"],
                    "returned_file_sanitized": returned["file"],
                    "returned_label": returned["label"],
                    "match_lines": returned.get("match_lines", []),
                    "elapsed_ms": result.get("elapsed_ms"),
                },
                "verified": True,
            }
        )

    index_status = run_cli(
        args.executable,
        shim,
        ["index_status", "--project", args.project],
    )
    if index_status.get("status") != "ready":
        raise RuntimeError(f"index is not ready: {index_status!r}")

    executable_version = subprocess.run(
        [str(args.executable), "--version"],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    receipt = {
        "schema_version": 1,
        "gate": "G1b",
        "component": "codebase-memory",
        "status": "pass",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "project": args.project,
        "index_root": index_status["root_path"],
        "index_counts": {
            "nodes": index_status["nodes"],
            "edges": index_status["edges"],
            "article_files": 520,
        },
        "tool": {
            "executable": str(args.executable),
            "version_output": (
                executable_version.stdout.strip()
                or executable_version.stderr.strip()
            ),
            "compatibility_shim": str(shim / "powershell.cmd"),
            "compatibility_reason": (
                "Official 0.9.0 invokes Windows PowerShell 5.1 without an "
                "explicit UTF-8 input encoding. The project-local shim routes "
                "that command to PowerShell 7, whose default file decoding "
                "preserves UTF-8 article paths."
            ),
            "known_limitation": (
                "The 0.9.0 JSON serializer replaces non-ASCII filename "
                "characters with '?'. The indexed result's preserved ASCII "
                "date-time prefix is therefore cross-checked against one "
                "unique local author_primary path."
            ),
        },
        "role_manifest": {
            "path": role_manifest.relative_to(root).as_posix(),
            "sha256": sha256_file(role_manifest),
        },
        "queries": records,
        "assertions": {
            "query_count": len(records),
            "years_covered": sorted({record["year"] for record in records}),
            "all_local_matches_unique": True,
            "all_matches_author_primary": True,
            "all_index_results_enriched": True,
            "all_returned_prefixes_match_expected": True,
            "article_path_filter": args.path_filter,
        },
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(output)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"G1b codebase-memory verification failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
