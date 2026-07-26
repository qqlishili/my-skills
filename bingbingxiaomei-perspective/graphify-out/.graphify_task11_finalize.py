import json
import runpy
from datetime import datetime, timezone
from pathlib import Path

from graphify.cache import check_semantic_cache, save_semantic_cache
from graphify.detect import detect, save_manifest


ROOT = Path(r"D:\Temp\create_skills\bingbingxiaomei-perspective")
OUT = ROOT / "graphify-out"
SEMANTIC_OUTPUTS = [
    OUT / ".graphify_task11_semantic_01.json",
    OUT / ".graphify_task11_semantic_02.json",
    OUT / ".graphify_task11_semantic_03.json",
]
EXPECTED_SOURCES = {
    ROOT / "SKILL.core.md",
    ROOT / "SKILL.md",
    ROOT / "docs" / "maintenance.md",
    ROOT / "evals" / "METHODOLOGY.md",
    ROOT / "references" / "heuristics" / "catalog.md",
    ROOT / "references" / "heuristics" / "legacy" / "h14-industry-belief.md",
    ROOT / "references" / "heuristics" / "legacy" / "h15-leverage-cleanup.md",
    ROOT / "references" / "heuristics" / "legacy" / "h16-liquidity-vs-business.md",
    ROOT / "references" / "heuristics" / "legacy" / "h17-active-loss-boundary.md",
    ROOT / "references" / "models" / "legacy" / "deep-1-three-elements.md",
    ROOT / "references" / "models" / "legacy" / "deep-4-competition.md",
    ROOT / "references" / "models" / "legacy" / "deep-9-ai-distillation.md",
    ROOT / "references" / "models" / "m01-three-elements-state.md",
    ROOT / "references" / "models" / "m02-risk-time-window.md",
    ROOT / "references" / "models" / "m03-strategic-industry-mapping.md",
    ROOT / "references" / "models" / "m04-industry-realization-chain.md",
    ROOT / "references" / "models" / "m05-evidence-state.md",
    ROOT / "references" / "models" / "m06-risk-budget.md",
    ROOT / "references" / "research" / "02-conversations.md",
    ROOT / "references" / "research" / "07-article-clusters.md",
    ROOT / "references" / "templates" / "article-interpretation.md",
    ROOT / "references" / "templates" / "deep-stock-report.md",
    ROOT / "references" / "templates" / "standard-stock-report.md",
}


def source_files(payload):
    values = set()
    for key in ("nodes", "edges", "hyperedges"):
        for item in payload.get(key, []):
            source = item.get("source_file")
            if source:
                values.add(Path(source).resolve())
    return values


def main():
    fresh = {"nodes": [], "edges": [], "hyperedges": []}
    covered = set()
    for path in SEMANTIC_OUTPUTS:
        payload = json.loads(path.read_text(encoding="utf-8"))
        for key in fresh:
            fresh[key].extend(payload.get(key, []))
        covered.update(source_files(payload))

    expected = {path.resolve() for path in EXPECTED_SOURCES}
    if covered != expected:
        missing = sorted(str(path) for path in expected - covered)
        extra = sorted(str(path) for path in covered - expected)
        raise SystemExit(f"semantic source mismatch: missing={missing}, extra={extra}")

    saved = save_semantic_cache(
        fresh["nodes"],
        fresh["edges"],
        fresh["hyperedges"],
        root=ROOT,
    )
    if saved != len(expected):
        raise SystemExit(f"expected {len(expected)} cached files, saved {saved}")

    detection = detect(ROOT)
    semantic_files = [
        *detection.get("files", {}).get("document", []),
        *detection.get("files", {}).get("paper", []),
        *detection.get("files", {}).get("image", []),
    ]
    nodes, edges, hyperedges, uncached = check_semantic_cache(
        semantic_files,
        root=ROOT,
    )
    if uncached:
        raise SystemExit(f"semantic cache still missing {len(uncached)} files: {uncached}")

    (OUT / ".graphify_detect.json").write_text(
        json.dumps(detection, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (OUT / ".graphify_semantic.json").write_text(
        json.dumps(
            {
                "nodes": nodes,
                "edges": edges,
                "hyperedges": hyperedges,
                "input_tokens": 0,
                "output_tokens": 0,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    runpy.run_path(str(OUT / ".graphify_run_ast.py"), run_name="__main__")
    runpy.run_path(str(OUT / ".graphify_build_codex.py"), run_name="__main__")
    save_manifest(
        detection["files"],
        manifest_path=str(OUT / "manifest.json"),
        kind="both",
        root=ROOT,
    )

    cost_path = OUT / "cost.json"
    cost = json.loads(cost_path.read_text(encoding="utf-8")) if cost_path.exists() else {"runs": []}
    cost.setdefault("runs", []).append(
        {
            "date": datetime.now(timezone.utc).isoformat(),
            "input_tokens": 0,
            "output_tokens": 0,
            "files": sum(len(paths) for paths in detection["files"].values()),
            "backend": "codex-host-agents",
            "usage_note": "subagent token usage unavailable from tool receipts",
        }
    )
    cost["total_input_tokens"] = sum(run.get("input_tokens", 0) for run in cost["runs"])
    cost["total_output_tokens"] = sum(run.get("output_tokens", 0) for run in cost["runs"])
    cost_path.write_text(json.dumps(cost, ensure_ascii=False, indent=2), encoding="utf-8")

    print(
        json.dumps(
            {
                "fresh_sources": len(covered),
                "semantic_files": len(semantic_files),
                "semantic_nodes": len(nodes),
                "semantic_edges": len(edges),
                "semantic_hyperedges": len(hyperedges),
                "uncached": len(uncached),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
