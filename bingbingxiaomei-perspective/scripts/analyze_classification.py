#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Analyze current taxonomy output or an explicit legacy artifact."""

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TAXONOMY_PATH = PROJECT_ROOT / "references" / "taxonomy.json"
DEFAULT_POINTER = (
    Path(__file__).resolve().parent / "classification_output" / "current.json"
)


def resolve_input_path(explicit_path=None, pointer_path=DEFAULT_POINTER):
    """Resolve an explicit artifact or the current-artifact pointer."""
    if explicit_path:
        path = Path(explicit_path)
        if not path.is_file():
            raise FileNotFoundError(f"classification artifact not found: {path}")
        return path

    pointer_path = Path(pointer_path)
    if not pointer_path.is_file():
        raise FileNotFoundError(
            f"current classification pointer not found: {pointer_path}"
        )
    raw = pointer_path.read_text(encoding="utf-8").strip()
    try:
        pointer = json.loads(raw)
    except json.JSONDecodeError:
        target = raw
    else:
        if isinstance(pointer, str):
            target = pointer
        elif isinstance(pointer, dict):
            target = pointer.get("path") or pointer.get("current")
        else:
            target = None
    if not target:
        raise ValueError(f"invalid current classification pointer: {pointer_path}")
    resolved = Path(target)
    if not resolved.is_absolute():
        resolved = pointer_path.parent / resolved
    if not resolved.is_file():
        raise FileNotFoundError(
            f"current classification artifact not found: {resolved}"
        )
    return resolved


def _load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _current_summary(data, taxonomy):
    model_ids = {item["id"] for item in taxonomy["models"]}
    heuristic_ids = {item["id"] for item in taxonomy["heuristics"]}
    model_counts = Counter()
    heuristic_counts = Counter()
    confidence_values = []
    unresolved_count = 0

    for article in data.get("per_article", []):
        model_id = article.get("primary_model_id")
        if model_id is not None and model_id not in model_ids:
            raise ValueError(f"unknown current model ID: {model_id}")
        if model_id:
            model_counts[model_id] += 1
        for candidate in article.get("model_candidates", []):
            if candidate["id"] not in model_ids:
                raise ValueError(
                    f"unknown current model candidate: {candidate['id']}"
                )
        for candidate in article.get("candidate_heuristics", []):
            heuristic_id = candidate["id"]
            if heuristic_id not in heuristic_ids:
                raise ValueError(
                    f"unknown current heuristic ID: {heuristic_id}"
                )
            heuristic_counts[heuristic_id] += 1
        confidence_values.append(float(article.get("confidence", 0)))
        unresolved_count += bool(article.get("unresolved"))

    return {
        "mode": "current",
        "total_articles": len(data.get("per_article", [])),
        "model_counts": dict(model_counts),
        "heuristic_counts": dict(heuristic_counts),
        "unresolved_count": unresolved_count,
        "average_confidence": (
            round(sum(confidence_values) / len(confidence_values), 3)
            if confidence_values
            else 0.0
        ),
        "corpus_digest": data.get("corpus_digest"),
        "taxonomy_digest": data.get("taxonomy_digest"),
    }


def _legacy_summary(data):
    model_counts = Counter()
    heuristic_counts = Counter()
    for article in data.get("per_article", []):
        for model in article.get("top_models", []):
            model_counts[model[0]] += 1
        for heuristic in article.get("top_heuristics", []):
            heuristic_counts[heuristic[0]] += 1
    return {
        "mode": "legacy",
        "total_articles": len(data.get("per_article", [])),
        "model_counts": dict(model_counts),
        "heuristic_counts": dict(heuristic_counts),
        "unresolved_count": None,
        "average_confidence": None,
        "corpus_digest": data.get("corpus_digest"),
        "taxonomy_digest": data.get("taxonomy_digest"),
    }


def analyze_file(path, taxonomy_path=TAXONOMY_PATH):
    """Analyze without mutating the source artifact."""
    data = _load_json(path)
    if data.get("schema_version") == 2:
        taxonomy_path = Path(taxonomy_path)
        taxonomy_raw = taxonomy_path.read_bytes()
        taxonomy_digest = hashlib.sha256(taxonomy_raw).hexdigest()
        if data.get("taxonomy_digest") != taxonomy_digest:
            raise ValueError(
                "taxonomy digest mismatch: artifact does not match current taxonomy"
            )
        taxonomy = json.loads(taxonomy_raw.decode("utf-8"))
        return _current_summary(data, taxonomy)
    return _legacy_summary(data)


def print_summary(summary, source):
    print(f"Source: {source}")
    print(f"Mode: {summary['mode']}")
    print(f"Total articles: {summary['total_articles']}")
    if summary["mode"] == "current":
        print(f"Unresolved: {summary['unresolved_count']}")
        print(f"Average confidence: {summary['average_confidence']:.3f}")
    print("Model counts:")
    for model_id, count in sorted(summary["model_counts"].items()):
        print(f"  {model_id}: {count}")
    print("Heuristic counts:")
    for heuristic_id, count in sorted(summary["heuristic_counts"].items()):
        print(f"  {heuristic_id}: {count}")


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "input",
        nargs="?",
        type=Path,
        help="explicit current or legacy classification JSON",
    )
    parser.add_argument("--pointer", type=Path, default=DEFAULT_POINTER)
    parser.add_argument("--taxonomy", type=Path, default=TAXONOMY_PATH)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    path = resolve_input_path(args.input, args.pointer)
    summary = analyze_file(path, args.taxonomy)
    print_summary(summary, path)
    return summary


if __name__ == "__main__":
    main()
