import json
import runpy
from datetime import datetime, timezone
from pathlib import Path

from graphify.cache import check_semantic_cache, save_semantic_cache
from graphify.detect import detect, save_manifest


ROOT = Path(r"D:\Temp\create_skills\bingbingxiaomei-perspective")
OUT = ROOT / "graphify-out"


def main():
    payload = json.loads(
        (OUT / ".graphify_task12_semantic.json").read_text(encoding="utf-8")
    )
    if save_semantic_cache(
        payload["nodes"], payload["edges"], payload["hyperedges"], root=ROOT
    ) != 2:
        raise SystemExit("expected exactly two refreshed semantic cache entries")

    detection = detect(ROOT)
    semantic_files = [
        *detection.get("files", {}).get("document", []),
        *detection.get("files", {}).get("paper", []),
        *detection.get("files", {}).get("image", []),
    ]
    nodes, edges, hyperedges, uncached = check_semantic_cache(
        semantic_files, root=ROOT
    )
    if uncached:
        raise SystemExit(f"semantic cache still missing: {uncached}")

    (OUT / ".graphify_detect.json").write_text(
        json.dumps(detection, ensure_ascii=False, indent=2), encoding="utf-8"
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
    cost = json.loads(cost_path.read_text(encoding="utf-8"))
    cost.setdefault("runs", []).append(
        {
            "date": datetime.now(timezone.utc).isoformat(),
            "input_tokens": 0,
            "output_tokens": 0,
            "files": sum(len(paths) for paths in detection["files"].values()),
            "backend": "codex-host-task12-incremental",
            "usage_note": "Two reviewed Markdown corrections; no external LLM call.",
        }
    )
    cost["total_input_tokens"] = sum(x.get("input_tokens", 0) for x in cost["runs"])
    cost["total_output_tokens"] = sum(x.get("output_tokens", 0) for x in cost["runs"])
    cost_path.write_text(json.dumps(cost, ensure_ascii=False, indent=2), encoding="utf-8")

    print(
        json.dumps(
            {
                "refreshed_sources": 2,
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
