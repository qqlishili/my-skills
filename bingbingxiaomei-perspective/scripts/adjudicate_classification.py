#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validate semantic reviews and build an immutable adjudicated artifact."""

import argparse
import hashlib
import json
from copy import deepcopy
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TAXONOMY_PATH = PROJECT_ROOT / "references" / "taxonomy.json"
OUTDIR = Path(__file__).resolve().parent / "classification_output"


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_taxonomy(path):
    raw = Path(path).read_bytes()
    return json.loads(raw.decode("utf-8")), hashlib.sha256(raw).hexdigest()


def require_canonical_current_target(taxonomy_path, outdir):
    """Reserve the project current pointer for the canonical taxonomy."""
    if Path(outdir).resolve() != OUTDIR.resolve():
        return
    if Path(taxonomy_path).resolve() != TAXONOMY_PATH.resolve():
        raise ValueError("default current requires the canonical taxonomy path")


def validate_review_coverage(expected_fnames, entries):
    """Require exact, duplicate-free coverage of the expected review set."""
    seen = set()
    for entry in entries:
        fname = entry.get("fname")
        if fname in seen:
            raise ValueError(f"duplicate review filename: {fname}")
        seen.add(fname)
    missing = sorted(set(expected_fnames) - seen)
    extra = sorted(seen - set(expected_fnames))
    if missing or extra:
        raise ValueError(
            "review coverage mismatch: "
            f"missing={len(missing)}, extra={len(extra)}"
        )
    return True


def validate_batch_metadata(batches, expected_count):
    """Require unique batches whose declared ranges exactly cover the queue."""
    def range_start(batch):
        declared = batch.get("unresolved_sorted_range")
        if isinstance(declared, dict):
            return declared.get("start_inclusive", -1)
        return -1

    seen_ids = set()
    cursor = 0
    for batch in sorted(batches, key=range_start):
        if batch.get("schema_version") != 1:
            raise ValueError("unsupported review batch schema version")
        batch_id = batch.get("batch_id")
        if batch_id in seen_ids:
            raise ValueError(f"duplicate review batch ID: {batch_id}")
        seen_ids.add(batch_id)
        declared = batch.get("unresolved_sorted_range")
        if not isinstance(declared, dict):
            raise ValueError("batch range must be an object")
        start = declared.get("start_inclusive")
        end = declared.get("end_exclusive")
        if not isinstance(start, int) or not isinstance(end, int):
            raise ValueError(f"batch range mismatch: {batch_id}")
        if start != cursor or end - start != len(batch.get("entries", [])):
            raise ValueError(f"batch range mismatch: {batch_id}")
        cursor = end
    if cursor != expected_count:
        raise ValueError(
            f"batch range mismatch: covered={cursor}, expected={expected_count}"
        )
    return True


def _validate_ids(entry, model_ids, heuristic_ids, batch_entry):
    if batch_entry:
        verdict = entry.get("model_verdict")
        if verdict not in {"resolved_to_model", "remains_unresolved"}:
            raise ValueError(f"invalid batch model verdict: {verdict}")
        primary = entry.get("expected_primary_model_id")
        if verdict == "resolved_to_model" and primary not in model_ids:
            raise ValueError(f"invalid resolved model ID: {primary}")
        if verdict == "remains_unresolved" and primary is not None:
            raise ValueError("remains_unresolved must not set a primary model")
        secondary = entry.get("secondary_model_ids", [])
        confidence = entry.get("confidence")
        if confidence not in {"high", "medium", "low"}:
            raise ValueError(f"invalid review confidence: {confidence}")
    else:
        verdict = entry.get("model_verdict")
        if verdict not in {"verified", "incorrect", "ambiguous"}:
            raise ValueError(f"invalid manual model verdict: {verdict}")
        primary = entry.get("expected_model_id")
        if primary not in model_ids:
            raise ValueError(f"invalid manual model ID: {primary}")
        secondary = []

    invalid_secondary = sorted(set(secondary) - model_ids)
    if invalid_secondary:
        raise ValueError(f"invalid secondary model IDs: {invalid_secondary}")
    invalid_heuristics = sorted(
        set(entry.get("supported_heuristic_ids", [])) - heuristic_ids
    )
    if invalid_heuristics:
        raise ValueError(f"invalid heuristic IDs: {invalid_heuristics}")


def _decision_from_manual(entry):
    ambiguous = entry["model_verdict"] == "ambiguous"
    return {
        "source": "resolved_model_sample_review",
        "model_verdict": entry["model_verdict"],
        "primary_model_id": None if ambiguous else entry["expected_model_id"],
        "secondary_model_ids": (
            [entry["expected_model_id"]] if ambiguous else []
        ),
        "verified_heuristic_ids": entry.get("supported_heuristic_ids", []),
        "confidence": "medium" if ambiguous else "high",
        "evidence_summary": entry.get("notes", ""),
        "rationale": entry.get("notes", ""),
    }


def _decision_from_batch(entry):
    return {
        "source": "unresolved_original_text_review",
        "model_verdict": entry["model_verdict"],
        "primary_model_id": entry.get("expected_primary_model_id"),
        "secondary_model_ids": entry.get("secondary_model_ids", []),
        "verified_heuristic_ids": entry.get("supported_heuristic_ids", []),
        "confidence": entry.get("confidence"),
        "evidence_summary": entry.get("evidence_summary", ""),
        "rationale": entry.get("rationale", ""),
    }


def adjudicate_output(
    raw_output,
    manual_review,
    batch_entries,
    taxonomy,
    taxonomy_digest,
    timestamp=None,
):
    """Overlay traceable review decisions while preserving classifier values."""
    if raw_output.get("classification_stage") not in {None, "raw"} or any(
        "classifier_primary_model_id" in article
        for article in raw_output.get("per_article", [])
    ):
        raise ValueError("adjudication requires a raw classification artifact")
    if raw_output.get("corpus_digest") != taxonomy.get("corpus_digest"):
        raise ValueError(
            "corpus digest mismatch: raw artifact is not canonical"
        )
    if raw_output.get("taxonomy_digest") != taxonomy_digest:
        raise ValueError(
            "taxonomy digest mismatch: raw artifact is not current"
        )

    model_ids = {item["id"] for item in taxonomy["models"]}
    heuristic_ids = {item["id"] for item in taxonomy["heuristics"]}
    decisions = {}

    for entry in manual_review.get("entries", []):
        _validate_ids(entry, model_ids, heuristic_ids, batch_entry=False)
        if entry["fname"] in decisions:
            raise ValueError(f"duplicate review filename: {entry['fname']}")
        decisions[entry["fname"]] = _decision_from_manual(entry)
    for entry in batch_entries:
        _validate_ids(entry, model_ids, heuristic_ids, batch_entry=True)
        if entry["fname"] in decisions:
            raise ValueError(f"duplicate review filename: {entry['fname']}")
        decisions[entry["fname"]] = _decision_from_batch(entry)

    output = deepcopy(raw_output)
    output["timestamp"] = timestamp or datetime.now().strftime(
        "%Y-%m-%dT%H%M%S%f"
    )
    output["raw_artifact_timestamp"] = raw_output.get("timestamp")
    output["classification_stage"] = "adjudicated"
    reviewed_total = 0
    reviewed_ending_resolved = 0
    originally_unresolved_resolved_by_review = 0
    originally_resolved_made_unresolved = 0
    remains_unresolved = 0

    for article in output.get("per_article", []):
        article["classifier_primary_model_id"] = article.get("primary_model_id")
        article["classifier_unresolved"] = bool(article.get("unresolved"))
        article["classifier_confidence"] = float(article.get("confidence", 0))
        decision = decisions.get(article.get("fname"))
        if not decision:
            continue
        reviewed_total += 1
        article["primary_model_id"] = decision["primary_model_id"]
        article["unresolved"] = decision["primary_model_id"] is None
        article["verified_heuristic_ids"] = decision["verified_heuristic_ids"]
        article["semantic_review"] = decision
        if article["unresolved"]:
            remains_unresolved += 1
            if not article["classifier_unresolved"]:
                originally_resolved_made_unresolved += 1
        else:
            reviewed_ending_resolved += 1
            if article["classifier_unresolved"]:
                originally_unresolved_resolved_by_review += 1

    unknown_reviews = sorted(
        set(decisions) - {article.get("fname") for article in output["per_article"]}
    )
    if unknown_reviews:
        raise ValueError(f"reviewed files absent from artifact: {unknown_reviews}")

    output["total_articles"] = len(output.get("per_article", []))
    output["unresolved_count"] = sum(
        bool(article.get("unresolved")) for article in output["per_article"]
    )
    output["adjudication"] = {
        "reviewed_total": reviewed_total,
        "reviewed_ending_resolved": reviewed_ending_resolved,
        "originally_unresolved_resolved_by_review": (
            originally_unresolved_resolved_by_review
        ),
        "originally_resolved_made_unresolved": (
            originally_resolved_made_unresolved
        ),
        "remains_unresolved_after_review": remains_unresolved,
        "manual_model_sample_total": len(manual_review.get("entries", [])),
        "unresolved_batch_total": len(batch_entries),
    }
    return output


def write_artifact(output, outdir=OUTDIR):
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / f"classification-adjudicated-{output['timestamp']}.json"
    with path.open("x", encoding="utf-8") as stream:
        json.dump(output, stream, ensure_ascii=False, indent=2)
    return path


def write_current_pointer(artifact_path, output, pointer_path):
    artifact_path = Path(artifact_path)
    pointer_path = Path(pointer_path)
    pointer = {
        "schema_version": 1,
        "path": artifact_path.name,
        "sha256": hashlib.sha256(artifact_path.read_bytes()).hexdigest(),
        "artifact_timestamp": output["timestamp"],
        "total_articles": output["total_articles"],
        "unresolved_count": output["unresolved_count"],
        "corpus_digest": output["corpus_digest"],
        "taxonomy_digest": output["taxonomy_digest"],
        "classification_stage": "adjudicated",
    }
    temporary = pointer_path.with_suffix(pointer_path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(pointer, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    temporary.replace(pointer_path)
    return pointer_path


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("raw_artifact", type=Path)
    parser.add_argument("--manual", type=Path, required=True)
    parser.add_argument("--batch", type=Path, action="append", required=True)
    parser.add_argument("--taxonomy", type=Path, default=TAXONOMY_PATH)
    parser.add_argument("--outdir", type=Path, default=OUTDIR)
    parser.add_argument("--update-current", action="store_true")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if args.update_current:
        require_canonical_current_target(args.taxonomy, args.outdir)
    raw_output = load_json(args.raw_artifact)
    taxonomy, taxonomy_digest = load_taxonomy(args.taxonomy)
    manual_review = load_json(args.manual)
    batches = [load_json(path) for path in args.batch]
    expected_unresolved = {
        article["fname"]
        for article in raw_output.get("per_article", [])
        if article.get("unresolved")
    }
    validate_batch_metadata(batches, len(expected_unresolved))
    batch_entries = [
        entry for batch in batches for entry in batch.get("entries", [])
    ]
    validate_review_coverage(expected_unresolved, batch_entries)
    output = adjudicate_output(
        raw_output,
        manual_review,
        batch_entries,
        taxonomy,
        taxonomy_digest,
    )
    artifact_path = write_artifact(output, args.outdir)
    print(f"Adjudicated classification saved to {artifact_path}")
    print(f"Reviewed: {output['adjudication']['reviewed_total']}")
    print(f"Unresolved after review: {output['unresolved_count']}")
    if args.update_current:
        pointer_path = write_current_pointer(
            artifact_path,
            output,
            args.outdir / "current.json",
        )
        print(f"Current classification pointer saved to {pointer_path}")
    return artifact_path


if __name__ == "__main__":
    main()
