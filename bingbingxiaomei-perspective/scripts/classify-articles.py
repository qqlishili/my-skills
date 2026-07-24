#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Route local articles to taxonomy candidates using primary-text matches."""

import argparse
import hashlib
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ARTICLES_DIR = PROJECT_ROOT / "references" / "sources" / "articles"
TAXONOMY_PATH = PROJECT_ROOT / "references" / "taxonomy.json"
OUTDIR = Path(__file__).resolve().parent / "classification_output"
DEFAULT_START = "2023-01-01"
DEFAULT_END = "2026-12-31"
TITLE_BOOST = 1
MIN_PRIMARY_MATCHES = 2
MAX_EVIDENCE_SNIPPETS = 3
TERM_PREFIXES = ("宏观", "中观", "微观", "市场", "国家", "当前", "整体")
TERM_SUFFIXES = ("状态模型", "模型", "启发式", "规则")


def load_taxonomy(path=TAXONOMY_PATH):
    """Load the canonical taxonomy and return it with its byte digest."""
    path = Path(path)
    raw = path.read_bytes()
    taxonomy = json.loads(raw.decode("utf-8"))
    model_ids = [item["id"] for item in taxonomy["models"]]
    heuristic_ids = [item["id"] for item in taxonomy["heuristics"]]
    if len(model_ids) != len(set(model_ids)):
        raise ValueError("taxonomy contains duplicate model IDs")
    if len(heuristic_ids) != len(set(heuristic_ids)):
        raise ValueError("taxonomy contains duplicate heuristic IDs")
    return taxonomy, hashlib.sha256(raw).hexdigest()


def _term_parts(value):
    """Extract conservative candidate terms from a taxonomy phrase."""
    parts = re.split(r"[/、，,；;：:（）()→\s]+", value)
    terms = set()
    for part in parts:
        part = part.strip("？?。.!！“”\"'`")
        if len(part) < 2:
            continue
        terms.add(part)
        for prefix in TERM_PREFIXES:
            if part.startswith(prefix) and len(part) - len(prefix) >= 2:
                terms.add(part[len(prefix) :])
        for suffix in TERM_SUFFIXES:
            if part.endswith(suffix) and len(part) - len(suffix) >= 2:
                terms.add(part[: -len(suffix)])
    return terms


def _route_terms(item, kind):
    values = [item["name"], item["definition"]]
    if kind == "model":
        values.extend(item.get("inputs", []))
        values.extend(item.get("applicable_questions", []))
    else:
        values.extend(item.get("applicable_scenarios", []))
    values.extend(
        evidence["quote"] for evidence in item.get("supporting_evidence", [])
    )

    terms = set()
    for value in values:
        terms.update(_term_parts(value))
    return sorted(terms, key=lambda term: (-len(term), term))


def build_routing_index(taxonomy):
    """Build candidate-only routing terms from the canonical taxonomy."""
    model_routes = {
        item["id"]: {
            "name": item["name"],
            "status": item["status"],
            "terms": item.get("routing_terms") or _route_terms(item, "model"),
        }
        for item in taxonomy["models"]
    }
    heuristic_routes = {
        item["id"]: {
            "name": item["name"],
            "status": item["status"],
            "terms": item.get("routing_terms")
            or _route_terms(item, "heuristic"),
        }
        for item in taxonomy["heuristics"]
    }
    return model_routes, heuristic_routes


def load_articles(
    start=None,
    end=None,
    articles_dir=ARTICLES_DIR,
):
    """Load local Markdown articles within an inclusive date range."""
    start = start or datetime.strptime(DEFAULT_START, "%Y-%m-%d")
    end = end or datetime.strptime(DEFAULT_END, "%Y-%m-%d")
    articles = []
    pattern = re.compile(
        r"(\d{4}-\d{2}-\d{2}) (\d{6})_冰冰小美_(.+)\.md"
    )

    for path in sorted(Path(articles_dir).glob("*.md")):
        match = pattern.fullmatch(path.name)
        if not match:
            continue
        date_text, time_text, title = match.groups()
        published_at = datetime.strptime(
            f"{date_text} {time_text}",
            "%Y-%m-%d %H%M%S",
        )
        if not start <= published_at <= end:
            continue
        body = path.read_text(encoding="utf-8")
        content = body.split("---", 2)[-1] if body.startswith("---") else body
        articles.append(
            {
                "date": date_text,
                "time": time_text,
                "dt": published_at,
                "title": title,
                "fname": path.name,
                "content": content,
                "len": len(content),
            }
        )

    return articles


def _matched_terms(text, title, route):
    body = text.casefold()
    title_text = title.casefold()
    matched = []
    score = 0
    for term in route["terms"]:
        normalized = term.casefold()
        if normalized in body:
            matched.append(term)
            score += 1
        if normalized in title_text:
            score += TITLE_BOOST
    return matched, score


def _candidate_list(text, title, routes):
    candidates = []
    for route_id, route in routes.items():
        matched, score = _matched_terms(text, title, route)
        if not matched:
            continue
        candidates.append(
            {
                "id": route_id,
                "name": route["name"],
                "status": route["status"],
                "score": score,
                "matched_terms": matched,
            }
        )
    return sorted(candidates, key=lambda item: (-item["score"], item["id"]))


def _evidence_snippets(text, candidates):
    lines = text.splitlines() or [text]
    snippets = []
    candidate_terms = {
        term
        for candidate in candidates
        for term in candidate["matched_terms"]
    }
    for line_number, line in enumerate(lines, start=1):
        compact = line.strip()
        if not compact:
            continue
        matched = sorted(
            (term for term in candidate_terms if term.casefold() in compact.casefold()),
            key=lambda term: (-len(term), term),
        )
        if matched:
            snippets.append(
                {
                    "line": line_number,
                    "text": compact[:500],
                    "matched_terms": matched,
                }
            )
        if len(snippets) >= MAX_EVIDENCE_SNIPPETS:
            break
    return snippets


def classify_article(article, model_routes, heuristic_routes):
    """Generate traceable candidates; never treat keyword hits as proof."""
    model_candidates = _candidate_list(
        article["content"],
        article["title"],
        model_routes,
    )
    heuristic_candidates = _candidate_list(
        article["content"],
        article["title"],
        heuristic_routes,
    )

    primary_model_id = None
    confidence = 0.0
    unresolved = True
    if model_candidates:
        top_score = model_candidates[0]["score"]
        confidence = min(0.95, 0.35 + 0.15 * top_score)
        tied = (
            len(model_candidates) > 1
            and model_candidates[1]["score"] == top_score
        )
        if top_score >= MIN_PRIMARY_MATCHES and not tied:
            primary_model_id = model_candidates[0]["id"]
            unresolved = False
        elif tied:
            confidence = min(confidence, 0.5)

    evidence = _evidence_snippets(
        article["content"],
        model_candidates + heuristic_candidates,
    )
    return {
        "article": (
            f"{article['date']} {article['time']}_{article['title']}"
        ),
        "fname": article["fname"],
        "primary_model_id": primary_model_id,
        "model_candidates": model_candidates,
        "candidate_heuristics": heuristic_candidates,
        "evidence_snippets": evidence,
        "confidence": round(confidence, 3),
        "unresolved": unresolved,
    }


def build_output(
    all_results,
    taxonomy,
    taxonomy_digest,
    corpus_digest,
    timestamp=None,
):
    """Build the current classification artifact contract."""
    return {
        "schema_version": 2,
        "timestamp": timestamp or datetime.now().strftime("%Y-%m-%dT%H%M%S"),
        "corpus_digest": corpus_digest,
        "taxonomy_digest": taxonomy_digest,
        "taxonomy_schema_version": taxonomy["schema_version"],
        "taxonomy_ids": {
            "models": [item["id"] for item in taxonomy["models"]],
            "heuristics": [item["id"] for item in taxonomy["heuristics"]],
        },
        "total_articles": len(all_results),
        "unresolved_count": sum(
            result["unresolved"] for result in all_results
        ),
        "per_article": all_results,
    }


def output_json(output, outdir=OUTDIR, prefix="classification"):
    """Write one immutable classification artifact."""
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / f"{prefix}-{output['timestamp']}.json"
    path.write_text(
        json.dumps(output, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path


def output_summary(output):
    model_counts = Counter(
        result["primary_model_id"]
        for result in output["per_article"]
        if result["primary_model_id"]
    )
    print(f"Total articles: {output['total_articles']}")
    print(f"Unresolved: {output['unresolved_count']}")
    for model_id, count in model_counts.most_common():
        print(f"{model_id}: {count}")


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default=DEFAULT_START)
    parser.add_argument("--end", default=DEFAULT_END)
    parser.add_argument("--taxonomy", type=Path, default=TAXONOMY_PATH)
    parser.add_argument("--articles-dir", type=Path, default=ARTICLES_DIR)
    parser.add_argument("--outdir", type=Path, default=OUTDIR)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    taxonomy, taxonomy_digest = load_taxonomy(args.taxonomy)
    model_routes, heuristic_routes = build_routing_index(taxonomy)
    articles = load_articles(
        datetime.strptime(args.start, "%Y-%m-%d"),
        datetime.strptime(args.end, "%Y-%m-%d"),
        args.articles_dir,
    )
    results = [
        classify_article(article, model_routes, heuristic_routes)
        for article in articles
    ]
    output = build_output(
        results,
        taxonomy,
        taxonomy_digest,
        taxonomy["corpus_digest"],
    )
    path = output_json(output, args.outdir)
    print(f"Classification results saved to {path}")
    output_summary(output)
    return path


if __name__ == "__main__":
    main()
