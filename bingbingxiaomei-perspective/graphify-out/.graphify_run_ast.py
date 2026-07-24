import json
from pathlib import Path

from graphify.extract import extract


def main():
    root = Path(r"D:\Temp\create_skills\bingbingxiaomei-perspective")
    out = root / "graphify-out"
    detection = json.loads((out / ".graphify_detect.json").read_text(encoding="utf-8"))
    code_files = [Path(path) for path in detection.get("files", {}).get("code", [])]
    result = (
        extract(code_files, cache_root=root)
        if code_files
        else {"nodes": [], "edges": [], "input_tokens": 0, "output_tokens": 0}
    )
    (out / ".graphify_ast.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "code_files": len(code_files),
                "ast_nodes": len(result.get("nodes", [])),
                "ast_edges": len(result.get("edges", [])),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
