import argparse
import ctypes
import hashlib
import json
import os
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path


EXIT_PASS = 0
EXIT_BLOCKED = 2
EXIT_DEFERRED = 3
EXIT_INVALID_STATE = 4

DEFAULT_TARGET = Path(r"D:\Temp\create_skills\bingbingxiaomei-perspective")
DEFAULT_VAULT = Path(r"D:\Temp\karpathy-llm-wiki-vault\raw\02-投资\01-xueqiu\冰冰小美")

FILE_ATTRIBUTE_REPARSE_POINT = 0x0400

VALID_MCP_KEYS = {"codebase_memory", "graphify", "codegraph"}
VALID_MCP_STATUSES = {"pending", "pass", "fail", "skipped", "deferred"}
VALID_STATUSES = VALID_MCP_STATUSES
FINAL_STATUSES = {"pass", "blocked", "deferred", "invalid_state"}


class LockHeldError(RuntimeError):
    pass


class UnsafeReparseTargetError(RuntimeError):
    pass


class SnapshotBlockedError(RuntimeError):
    def __init__(self, details):
        self.details = details
        super().__init__(details.get("blocked_reason", "snapshot blocked"))


def articles_dir(target=DEFAULT_TARGET):
    return Path(target) / "references" / "sources" / "articles"


def state_path(target=DEFAULT_TARGET):
    return Path(target) / ".preflight-state.json"


def lock_path(target=DEFAULT_TARGET):
    return Path(target) / ".preflight.lock"


def utc_now():
    return datetime.now(timezone.utc)


def utc_now_iso():
    return utc_now().replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_utc(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_json(value):
    data = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256_bytes(data)


def file_sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def has_reparse_flag(attributes):
    return bool(attributes & FILE_ATTRIBUTE_REPARSE_POINT)


def get_file_attributes(path):
    if os.name != "nt":
        return 0
    attrs = ctypes.windll.kernel32.GetFileAttributesW(str(Path(path)))
    if attrs == 0xFFFFFFFF:
        return 0
    return attrs


def is_reparse_point(path):
    return has_reparse_flag(get_file_attributes(path))


def _relative_posix(path, root):
    return Path(path).relative_to(root).as_posix()


def scan_markdown_root(root):
    root = Path(root)
    files = []
    reparse_skipped = []
    if not root.exists():
        return {"corpus_digest": sha256_json([]), "file_count": 0, "total_bytes": 0, "files": [], "reparse_skipped": []}

    for current, dirs, names in os.walk(root, followlinks=False):
        current_path = Path(current)
        kept_dirs = []
        for name in sorted(dirs):
            child = current_path / name
            if is_reparse_point(child):
                reparse_skipped.append(_relative_posix(child, root))
            else:
                kept_dirs.append(name)
        dirs[:] = kept_dirs

        for name in sorted(names):
            path = current_path / name
            if path.suffix.lower() != ".md":
                continue
            if is_reparse_point(path):
                reparse_skipped.append(_relative_posix(path, root))
                continue
            data = path.read_bytes()
            files.append({"path": _relative_posix(path, root), "sha256": sha256_bytes(data), "bytes": len(data)})

    files.sort(key=lambda item: item["path"])
    return {
        "corpus_digest": sha256_json(files),
        "file_count": len(files),
        "total_bytes": sum(item["bytes"] for item in files),
        "files": files,
        "reparse_skipped": sorted(reparse_skipped),
    }


def scan_corpus(target=DEFAULT_TARGET):
    return scan_markdown_root(articles_dir(target))


class PreflightLock:
    def __init__(self, path, stale_after_seconds=None):
        self.path = Path(path)
        self.stale_after_seconds = stale_after_seconds
        self.fd = None

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self._is_stale():
            self.path.unlink(missing_ok=True)
        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
        try:
            self.fd = os.open(str(self.path), flags)
        except FileExistsError as exc:
            raise LockHeldError(f"preflight lock held: {self.path}") from exc
        payload = {"pid": os.getpid(), "started_at": utc_now_iso()}
        os.write(self.fd, json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"))
        return self

    def __exit__(self, exc_type, exc, tb):
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None
        self.path.unlink(missing_ok=True)

    def _is_stale(self):
        if self.stale_after_seconds is None or not self.path.exists():
            return False
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            started_at = parse_utc(data["started_at"])
        except Exception:
            return True
        age = (utc_now() - started_at).total_seconds()
        return age > self.stale_after_seconds


def write_state(path, state):
    if state.get("schema_version") != 1:
        raise ValueError("state schema_version must be 1")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump(state, f, ensure_ascii=False, indent=2, sort_keys=True)
            f.write("\n")
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def read_state(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def ensure_real_directory_target(path):
    path = Path(path)
    if is_reparse_point(path):
        raise UnsafeReparseTargetError(f"refusing reparse target: {path}")
    path.mkdir(parents=True, exist_ok=True)
    if is_reparse_point(path):
        raise UnsafeReparseTargetError(f"refusing reparse target: {path}")
    return path


def copy_to_staging(source, staging):
    source = Path(source)
    staging = Path(staging)
    if staging.exists():
        shutil.rmtree(staging)
    shutil.copytree(source, staging, symlinks=False)
    return staging


def sync_real_directory(source, target):
    source = Path(source)
    target = ensure_real_directory_target(target)
    if is_reparse_point(target):
        raise UnsafeReparseTargetError(f"refusing reparse target: {target}")
    staging = target.parent / (target.name + ".staging")
    copy_to_staging(source, staging)
    copied_files = sum(1 for item in staging.rglob("*") if item.is_file())
    if target.exists():
        shutil.rmtree(target)
    os.replace(staging, target)
    return {"copied_files": copied_files, "target": str(target)}


def _relative_files(root):
    root = Path(root)
    if not root.exists():
        return set()
    return {
        item.relative_to(root).as_posix()
        for item in root.rglob("*")
        if item.is_file() and not is_reparse_point(item)
    }


def _copy_update_real_directory(source, target):
    source = Path(source)
    target = ensure_real_directory_target(target)
    copied_files = 0
    for source_file in sorted(item for item in source.rglob("*") if item.is_file()):
        if is_reparse_point(source_file):
            continue
        relative = source_file.relative_to(source).as_posix()
        target_file = target / relative
        target_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_file, target_file)
        copied_files += 1
    return {"copied_files": copied_files}


def _replace_reparse_with_staging(reparse_path, staging):
    reparse_path = Path(reparse_path)
    staging = Path(staging)
    if reparse_path.exists():
        if reparse_path.is_dir():
            os.rmdir(reparse_path)
        else:
            reparse_path.unlink()
    os.replace(staging, reparse_path)


def prepare_corpus_snapshot(target, vault, after_copy=None, replace_reparse_hook=None):
    target = Path(target)
    vault = Path(vault)
    target_articles = articles_dir(target)
    source_before = scan_markdown_root(vault)
    target_articles.parent.mkdir(parents=True, exist_ok=True)
    reparse_skipped = []
    target_only_files = []

    if is_reparse_point(target_articles):
        staging = Path(tempfile.mkdtemp(prefix=target_articles.name + ".staging.", dir=str(target_articles.parent)))
        try:
            copy_to_staging(vault, staging)
            staging_scan = scan_markdown_root(staging)
            if staging_scan["corpus_digest"] != source_before["corpus_digest"]:
                raise SnapshotBlockedError({
                    "snapshot_status": "blocked",
                    "blocked_reason": "staging digest does not match source_before digest",
                    "source_before_digest": source_before["corpus_digest"],
                    "source_after_digest": source_before["corpus_digest"],
                    "staging_digest": staging_scan["corpus_digest"],
                    "target_only_files": [],
                    "reparse_skipped": reparse_skipped,
                })
            if after_copy:
                after_copy()
            source_after = scan_markdown_root(vault)
            if source_after["corpus_digest"] != source_before["corpus_digest"]:
                raise SnapshotBlockedError({
                    "snapshot_status": "blocked",
                    "blocked_reason": "source changed during snapshot",
                    "source_before_digest": source_before["corpus_digest"],
                    "source_after_digest": source_after["corpus_digest"],
                    "target_only_files": [],
                    "reparse_skipped": reparse_skipped,
                })
            replace = replace_reparse_hook or _replace_reparse_with_staging
            replace(target_articles, staging)
            staging = None
            status = "migrated_reparse"
        finally:
            if staging is not None and staging.exists():
                shutil.rmtree(staging)
    else:
        target_only_files = sorted(_relative_files(target_articles) - _relative_files(vault))
        if target_only_files:
            raise SnapshotBlockedError({
                "snapshot_status": "blocked",
                "blocked_reason": "target-only files would be removed by normal sync",
                "source_before_digest": source_before["corpus_digest"],
                "source_after_digest": source_before["corpus_digest"],
                "target_only_files": target_only_files,
                "reparse_skipped": reparse_skipped,
            })
        _copy_update_real_directory(vault, target_articles)
        if after_copy:
            after_copy()
        source_after = scan_markdown_root(vault)
        if source_after["corpus_digest"] != source_before["corpus_digest"]:
            raise SnapshotBlockedError({
                "snapshot_status": "blocked",
                "blocked_reason": "source changed during snapshot",
                "source_before_digest": source_before["corpus_digest"],
                "source_after_digest": source_after["corpus_digest"],
                "target_only_files": target_only_files,
                "reparse_skipped": reparse_skipped,
            })
        status = "synced"

    return {
        "snapshot_status": status,
        "source_before_digest": source_before["corpus_digest"],
        "source_after_digest": source_after["corpus_digest"],
        "target_only_files": target_only_files,
        "reparse_skipped": reparse_skipped,
    }


def build_index_plan(corpus, previous_state=None, script_digest=None):
    previous_state = previous_state or {}
    previous_pass_digest = previous_state.get("previous_pass_digest")
    previous_script_digest = previous_state.get("script_digest") or previous_state.get("index_plan", {}).get("script_digest")
    corpus_digest = corpus["corpus_digest"]
    content_changed = corpus_digest != previous_pass_digest
    script_changed = previous_script_digest is not None and script_digest != previous_script_digest

    requirements = {
        "codebase_memory": {"required": content_changed, "reason": "article corpus digest changed" if content_changed else "no content change"},
        "graphify": {"required": content_changed, "reason": "article corpus digest changed" if content_changed else "no content change"},
        "codegraph": {"required": script_changed, "reason": "preflight script changed" if script_changed else "script unchanged or no prior script digest"},
    }
    action = "index_required" if any(item["required"] for item in requirements.values()) else "no_content_change"
    return {
        "action": action,
        "previous_pass_digest": previous_pass_digest,
        "corpus_digest": corpus_digest,
        "script_digest": script_digest,
        "requirements": requirements,
    }


def _required_mcp_keys(state):
    requirements = state.get("index_plan", {}).get("requirements", {})
    return {key for key, info in requirements.items() if info.get("required")}


def _has_valid_receipts(state):
    if state.get("schema_version") != 1:
        return False
    corpus = state.get("corpus")
    if not isinstance(corpus, dict) or not corpus.get("corpus_digest"):
        return False
    index_plan = state.get("index_plan")
    if not isinstance(index_plan, dict):
        return False
    requirements = index_plan.get("requirements")
    if not isinstance(requirements, dict):
        return False
    if index_plan.get("action") == "no_content_change" and state.get("previous_pass_digest") != corpus.get("corpus_digest"):
        return False
    for key, requirement in requirements.items():
        if key not in VALID_MCP_KEYS:
            return False
        if not isinstance(requirement, dict) or "required" not in requirement:
            return False
    return True


def final_status(state):
    if state.get("snapshot_status") == "blocked":
        return "blocked"
    if not _has_valid_receipts(state):
        return "invalid_state"
    required = _required_mcp_keys(state)
    mcp = state.get("mcp", {})
    required_statuses = [mcp.get(key, {}).get("status") for key in required]
    if any(status == "fail" for status in required_statuses):
        return "blocked"
    if any(status != "pass" for status in required_statuses):
        return "deferred"
    if any(result.get("status") == "fail" for result in mcp.values()):
        return "blocked"
    return "pass"


def exit_code_for_status(status):
    if status == "pass":
        return EXIT_PASS
    if status == "blocked":
        return EXIT_BLOCKED
    if status == "deferred":
        return EXIT_DEFERRED
    return EXIT_INVALID_STATE


def apply_final_status(state):
    updated = dict(state)
    status = final_status(updated)
    updated["final_status"] = status
    updated["finalized_at"] = utc_now_iso()
    if status == "pass":
        updated["previous_pass_digest"] = updated.get("corpus", {}).get("corpus_digest")
    return updated


def graphify_env():
    return {
        "ANTHROPIC_BASE_URL": "http://127.0.0.1:15721",
        "ANTHROPIC_API_KEY": "ccswitch-proxy",
    }


def codegraph_command(target=DEFAULT_TARGET):
    return rf"C:\Users\LiN\AppData\Local\codegraph\current\bin\codegraph.cmd index --force {Path(target)}"


def graphify_command(target=DEFAULT_TARGET):
    return rf"C:\Users\LiN\.workbuddy\binaries\python\envs\default\Scripts\graphify.exe ."


def _is_external_source(source):
    normalized = source.replace("\\", "/")
    parts = [part for part in normalized.split("/") if part]
    return (
        normalized.startswith("/")
        or normalized.startswith("//")
        or (len(normalized) >= 3 and normalized[1] == ":" and normalized[2] == "/" and normalized[0].isalpha())
        or ".." in parts
    )


def _semantic_hits_value(value, errors):
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        errors.append(f"semantic_hits is not numeric: {value!r}")
        return 0


def verify_graphify_graph(graph, graphify_required=False):
    nodes = graph.get("nodes") or []
    links = graph.get("links") or graph.get("edges") or []
    errors = []
    if not nodes:
        errors.append("graph has no nodes")
    if not links:
        errors.append("graph has no links")

    article_count = 0
    for node in nodes:
        source = str(node.get("source_file") or node.get("file") or "")
        normalized = source.replace("\\", "/")
        if source and _is_external_source(source):
            errors.append(f"unexpected external source: {source}")
        if normalized.startswith("articles/") or "/articles/" in normalized:
            article_count += 1

    if graphify_required and article_count <= 0:
        errors.append("graphify required but no article source_file nodes found")
    semantic_hits = _semantic_hits_value(graph.get("semantic_hits", 0), errors)
    if semantic_hits <= 0:
        errors.append("semantic_hits must be > 0")

    return {
        "status": "fail" if errors else "pass",
        "errors": errors,
        "nodes": len(nodes),
        "links": len(links),
        "article_source_files": article_count,
        "semantic_hits": semantic_hits,
    }


def record_mcp_result(state, key, status, details=None):
    if key not in VALID_MCP_KEYS:
        raise ValueError(f"invalid MCP key: {key}")
    if status not in VALID_MCP_STATUSES:
        raise ValueError(f"invalid MCP status: {status}")
    state.setdefault("mcp", {})[key] = {
        "status": status,
        "recorded_at": utc_now_iso(),
        "details": details or {},
    }
    return state


def render_status(state):
    status = final_status(state)
    target = state.get("preflight_target") or state.get("target") or str(DEFAULT_TARGET)
    lines = [
        f"Preflight target: {str(target).replace(chr(92), '/')}",
        f"Status: {status}",
        f"Previous pass: {str(bool(state.get('previous_pass_digest'))).lower()}",
        f"schema_version: {state.get('schema_version')}",
        f"final_status: {status}",
    ]
    plan = state.get("index_plan", {})
    if plan:
        lines.append(f"index_plan: {plan.get('action')}")
    for key in sorted(VALID_MCP_KEYS):
        status = state.get("mcp", {}).get(key, {}).get("status", "pending")
        lines.append(f"{key}: {status}")
    return "\n".join(lines)


def _load_previous_state(path):
    if Path(path).exists():
        return read_state(path)
    return {}


def _mcp_for_plan(previous_mcp, index_plan):
    mcp = dict(previous_mcp or {})
    for key, requirement in index_plan.get("requirements", {}).items():
        if requirement.get("required"):
            mcp[key] = {"status": "pending", "recorded_at": utc_now_iso(), "details": {"reset_reason": "required_by_current_plan"}}
    return mcp


def prepare(target):
    target = Path(target)
    state_file = state_path(target)
    previous = _load_previous_state(state_file)
    try:
        snapshot = prepare_corpus_snapshot(target, DEFAULT_VAULT)
    except SnapshotBlockedError as exc:
        corpus = scan_corpus(target)
        state = {
            "schema_version": 1,
            "prepared_at": utc_now_iso(),
            "target": str(target),
            "preflight_target": str(target),
            "vault": str(DEFAULT_VAULT),
            "corpus": corpus,
            **exc.details,
        }
        write_state(state_file, state)
        return state
    corpus = scan_corpus(target)
    script_digest = file_sha256(__file__)
    index_plan = build_index_plan(corpus, previous, script_digest=script_digest)
    state = {
        "schema_version": 1,
        "prepared_at": utc_now_iso(),
        "target": str(target),
        "preflight_target": str(target),
        "vault": str(DEFAULT_VAULT),
        "corpus": corpus,
        "script_digest": script_digest,
        **snapshot,
        "index_plan": index_plan,
        "mcp": _mcp_for_plan(previous.get("mcp", {}), index_plan),
    }
    write_state(state_file, state)
    return state


def build_parser():
    parser = argparse.ArgumentParser(description="Article corpus preflight")
    parser.add_argument("--target", default=str(DEFAULT_TARGET))
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("prepare").add_argument("--target", default=argparse.SUPPRESS)
    subparsers.add_parser("status").add_argument("--target", default=argparse.SUPPRESS)
    subparsers.add_parser("finalize").add_argument("--target", default=argparse.SUPPRESS)
    record = subparsers.add_parser("record-mcp")
    record.add_argument("key")
    record.add_argument("status")
    record.add_argument("--target", default=argparse.SUPPRESS)
    record.add_argument("--details-json", default="{}")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    target = Path(args.target)
    state_file = state_path(target)

    if args.command == "prepare":
        state = prepare(target)
        print(render_status(state))
        return exit_code_for_status(final_status(state))

    if args.command == "status":
        state = read_state(state_file)
        print(render_status(state))
        return exit_code_for_status(final_status(state))

    if args.command == "record-mcp":
        state = read_state(state_file)
        details = json.loads(args.details_json)
        record_mcp_result(state, args.key, args.status, details)
        state = apply_final_status(state)
        write_state(state_file, state)
        print(render_status(state))
        return exit_code_for_status(final_status(state))

    if args.command == "finalize":
        state = apply_final_status(read_state(state_file))
        write_state(state_file, state)
        print(render_status(state))
        return exit_code_for_status(state["final_status"])

    return EXIT_INVALID_STATE


if __name__ == "__main__":
    sys.exit(main())
