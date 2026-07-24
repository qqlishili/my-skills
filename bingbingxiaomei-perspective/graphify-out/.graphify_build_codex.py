import json
from pathlib import Path

from graphify.analyze import god_nodes, surprising_connections, suggest_questions
from graphify.build import build_from_json
from graphify.cluster import cluster, score_all
from graphify.diagnostics import diagnose_extraction
from graphify.export import to_json
from graphify.report import generate


def main():
    root = Path(r"D:\Temp\create_skills\bingbingxiaomei-perspective")
    out = root / "graphify-out"
    ast = json.loads((out / ".graphify_ast.json").read_text(encoding="utf-8"))
    semantic = json.loads(
        (out / ".graphify_semantic.json").read_text(encoding="utf-8")
    )
    detection = json.loads(
        (out / ".graphify_detect.json").read_text(encoding="utf-8")
    )

    seen = {node["id"] for node in ast["nodes"]}
    nodes = list(ast["nodes"])
    for node in semantic["nodes"]:
        if node["id"] not in seen:
            nodes.append(node)
            seen.add(node["id"])
    extraction = {
        "nodes": nodes,
        "edges": ast["edges"] + semantic["edges"],
        "hyperedges": semantic.get("hyperedges", []),
        "input_tokens": semantic.get("input_tokens", 0),
        "output_tokens": semantic.get("output_tokens", 0),
    }
    (out / ".graphify_extract.json").write_text(
        json.dumps(extraction, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    health = diagnose_extraction(extraction, directed=False, root=root)
    graph = build_from_json(extraction, root=root, directed=False)
    if graph.number_of_nodes() == 0:
        raise SystemExit("Graph is empty")
    communities = cluster(graph)
    cohesion = score_all(graph, communities)
    labels = {community_id: f"Community {community_id}" for community_id in communities}
    tokens = {
        "input": extraction.get("input_tokens", 0),
        "output": extraction.get("output_tokens", 0),
    }
    gods = god_nodes(graph)
    surprises = surprising_connections(graph, communities)
    questions = suggest_questions(graph, communities, labels)

    if not to_json(graph, communities, out / "graph.json"):
        raise SystemExit("Graph export refused to overwrite existing graph")
    report = generate(
        graph,
        communities,
        cohesion,
        labels,
        gods,
        surprises,
        detection,
        tokens,
        root,
        suggested_questions=questions,
    )
    (out / "GRAPH_REPORT.md").write_text(report, encoding="utf-8")
    analysis = {
        "communities": {str(key): value for key, value in communities.items()},
        "cohesion": {str(key): value for key, value in cohesion.items()},
        "gods": gods,
        "surprises": surprises,
        "questions": questions,
    }
    (out / ".graphify_analysis.json").write_text(
        json.dumps(analysis, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "nodes": graph.number_of_nodes(),
                "edges": graph.number_of_edges(),
                "communities": len(communities),
                "health": health,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
