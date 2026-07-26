"""Validate cross-object invariants for an article interpretation brief.

JSON Schema owns shape and closed enums. This validator owns invariants that
Draft 2020-12 cannot express portably, such as ID uniqueness and references.
"""

from pathlib import PurePosixPath


AUTHOR_ROLES = {"author_post", "author_reply"}
RELATIONS = {
    "repeats",
    "extends",
    "narrows",
    "revises",
    "contradicts",
    "applies",
    "no_evidence",
}


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _validate_span(span, label):
    start = span.get("start_line")
    end = span.get("end_line")
    _require(isinstance(start, int) and start >= 1, f"{label}: invalid start_line")
    _require(isinstance(end, int) and end >= start, f"{label}: invalid end_line")


def _validate_evidence(evidence, label):
    path = evidence.get("article_path", "")
    parts = PurePosixPath(path).parts
    _require(
        path.startswith("references/sources/articles/")
        and path.endswith(".md")
        and ".." not in parts,
        f"{label}: invalid article_path",
    )
    _require(evidence.get("role") in AUTHOR_ROLES, f"{label}: non-author role")
    _require(
        evidence.get("evidence_eligibility") == "author_primary",
        f"{label}: evidence is not author_primary",
    )
    _require(
        evidence.get("verified_against_primary_text") is True,
        f"{label}: primary text was not verified",
    )
    _validate_span(evidence.get("line_span", {}), f"{label}.line_span")


def validate_article_brief(brief):
    """Raise ValueError when a cross-object contract invariant is violated."""

    _require(brief.get("schema_version") == 1, "unsupported schema_version")
    _require(brief.get("input", {}).get("input_mode") == "ephemeral", "input is not ephemeral")

    segments = brief.get("input_segments", [])
    segment_by_id = {}
    for index, segment in enumerate(segments):
        segment_id = segment.get("segment_id")
        _require(segment_id and segment_id not in segment_by_id, "duplicate segment_id")
        _validate_span(segment.get("line_span", {}), f"input_segments[{index}].line_span")
        segment_by_id[segment_id] = segment

    claim_ids = set()
    for index, result in enumerate(brief.get("claim_results", [])):
        claim = result.get("claim", {})
        relation = result.get("historical_relation", {})
        claim_id = claim.get("claim_id")
        _require(claim_id and claim_id not in claim_ids, "duplicate claim_id")
        claim_ids.add(claim_id)

        segment_id = claim.get("input_segment_id")
        _require(segment_id in segment_by_id, f"{claim_id}: unknown input_segment_id")
        actual_role = segment_by_id[segment_id].get("role")
        _require(
            claim.get("input_segment_role") == actual_role,
            f"{claim_id}: input segment role mismatch",
        )
        claim_type = claim.get("claim_type")
        if actual_role == "analyst_text":
            _require(claim_type == "analyst_inference", f"{claim_id}: analyst text misattributed")
        elif actual_role == "external_context":
            _require(claim_type == "external_fact", f"{claim_id}: external context misattributed")
        elif actual_role == "unknown":
            _require(
                claim_type in {"analyst_inference", "external_fact"},
                f"{claim_id}: unknown source attributed to author",
            )
        if brief.get("document_type") in {"secondary_analysis", "unknown"}:
            _require(
                claim_type != "author_judgement",
                f"{claim_id}: non-primary document attributed as author judgement",
            )
        _validate_span(claim.get("source_span", {}), f"{claim_id}.source_span")

        relation_name = relation.get("relation")
        _require(relation_name in RELATIONS, f"{claim_id}: invalid relation")
        evidence_items = relation.get("historical_evidence", [])
        if relation_name == "no_evidence":
            _require(not evidence_items, f"{claim_id}: no_evidence has evidence")
        else:
            _require(evidence_items, f"{claim_id}: relation lacks author evidence")
        for evidence_index, evidence in enumerate(evidence_items):
            _validate_evidence(evidence, f"claim_results[{index}].evidence[{evidence_index}]")

    mapping = brief.get("taxonomy_mapping", {})
    if mapping.get("status") == "unavailable_before_G2":
        _require(not mapping.get("model_ids"), "unavailable mapping contains model IDs")
        _require(not mapping.get("heuristic_ids"), "unavailable mapping contains heuristic IDs")

    for key in ("supporting_evidence", "counter_evidence"):
        for index, evidence in enumerate(brief.get(key, [])):
            _validate_evidence(evidence, f"{key}[{index}]")


__all__ = ["validate_article_brief"]
