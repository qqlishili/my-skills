import json
from pathlib import Path

from graphify.analyze import suggest_questions
from graphify.build import build_from_json
from graphify.report import generate


def main():
    root = Path(r"D:\Temp\create_skills\bingbingxiaomei-perspective")
    out = root / "graphify-out"
    extraction = json.loads(
        (out / ".graphify_extract.json").read_text(encoding="utf-8")
    )
    detection = json.loads(
        (out / ".graphify_detect.json").read_text(encoding="utf-8")
    )
    analysis = json.loads(
        (out / ".graphify_analysis.json").read_text(encoding="utf-8")
    )

    labels = {}
    for batch_number in range(1, 5):
        batch = json.loads(
            (out / f".graphify_label_batch_{batch_number:02d}.json").read_text(
                encoding="utf-8"
            )
        )
        labels.update({int(key): value for key, value in batch["labels"].items()})

    expected = {int(key) for key in analysis["communities"]}
    if set(labels) != expected:
        missing = sorted(expected - set(labels))
        extra = sorted(set(labels) - expected)
        raise SystemExit(f"Community label mismatch: missing={missing}, extra={extra}")

    graph = build_from_json(extraction, root=root, directed=False)
    communities = {
        int(key): value for key, value in analysis["communities"].items()
    }
    cohesion = {int(key): value for key, value in analysis["cohesion"].items()}
    tokens = {
        "input": extraction.get("input_tokens", 0),
        "output": extraction.get("output_tokens", 0),
    }
    questions = suggest_questions(graph, communities, labels)
    report = generate(
        graph,
        communities,
        cohesion,
        labels,
        analysis["gods"],
        analysis["surprises"],
        detection,
        tokens,
        root,
        suggested_questions=questions,
    )
    (out / "GRAPH_REPORT.md").write_text(report, encoding="utf-8")
    (out / ".graphify_labels.json").write_text(
        json.dumps({str(key): value for key, value in labels.items()}, ensure_ascii=False),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "labels": len(labels),
                "questions": len(questions),
                "report": str(out / "GRAPH_REPORT.md"),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
