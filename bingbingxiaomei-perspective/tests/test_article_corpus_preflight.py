import importlib.util
import json
import os
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest import mock


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "article_corpus_preflight.py"
)
spec = importlib.util.spec_from_file_location("article_corpus_preflight", MODULE_PATH)
preflight = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preflight)


class ArticleCorpusPreflightTests(unittest.TestCase):
    def call_main(self, argv):
        with redirect_stdout(StringIO()):
            return preflight.main(argv)

    def test_default_paths_and_constants(self):
        self.assertEqual(preflight.EXIT_PASS, 0)
        self.assertEqual(preflight.EXIT_BLOCKED, 2)
        self.assertEqual(preflight.EXIT_DEFERRED, 3)
        self.assertEqual(preflight.EXIT_INVALID_STATE, 4)
        self.assertEqual(
            preflight.DEFAULT_TARGET,
            Path(r"D:\Temp\create_skills\bingbingxiaomei-perspective"),
        )
        self.assertEqual(
            preflight.DEFAULT_VAULT,
            Path(r"D:\Temp\karpathy-llm-wiki-vault\raw\02-投资\01-xueqiu\冰冰小美"),
        )

    def test_path_helpers(self):
        root = Path(tempfile.mkdtemp())
        self.assertEqual(preflight.articles_dir(root), root / "references" / "sources" / "articles")
        self.assertEqual(preflight.state_path(root), root / ".preflight-state.json")
        self.assertEqual(preflight.lock_path(root), root / ".preflight.lock")

    def test_scan_corpus_hashes_markdown_content_only(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            articles = preflight.articles_dir(root)
            articles.mkdir(parents=True)
            (articles / "b.txt").write_text("ignored", encoding="utf-8")
            (articles / "a.md").write_text("alpha", encoding="utf-8")
            (articles / "nested").mkdir()
            (articles / "nested" / "c.md").write_text("gamma", encoding="utf-8")

            scan = preflight.scan_corpus(root)

            self.assertEqual(scan["file_count"], 2)
            self.assertEqual(scan["total_bytes"], len("alpha".encode()) + len("gamma".encode()))
            self.assertEqual([f["path"] for f in scan["files"]], ["a.md", "nested/c.md"])
            expected_file_digest = preflight.sha256_bytes(b"alpha")
            self.assertEqual(scan["files"][0]["sha256"], expected_file_digest)
            expected_corpus = preflight.sha256_json(
                [
                    {"path": "a.md", "sha256": preflight.sha256_bytes(b"alpha"), "bytes": 5},
                    {"path": "nested/c.md", "sha256": preflight.sha256_bytes(b"gamma"), "bytes": 5},
                ]
            )
            self.assertEqual(scan["corpus_digest"], expected_corpus)

    def test_scan_corpus_skips_nested_reparse_points(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            articles = preflight.articles_dir(root)
            articles.mkdir(parents=True)
            skipped = articles / "skip"
            skipped.mkdir()
            (skipped / "hidden.md").write_text("hidden", encoding="utf-8")
            (articles / "visible.md").write_text("visible", encoding="utf-8")

            with mock.patch.object(preflight, "is_reparse_point", side_effect=lambda p: p == skipped):
                scan = preflight.scan_corpus(root)

            self.assertEqual(scan["file_count"], 1)
            self.assertEqual(scan["files"][0]["path"], "visible.md")
            self.assertEqual(scan["reparse_skipped"], ["skip"])

    def test_preflight_lock_exclusive_and_stale(self):
        with tempfile.TemporaryDirectory() as td:
            lock_file = Path(td) / "lock.json"
            with preflight.PreflightLock(lock_file):
                self.assertTrue(lock_file.exists())
                with self.assertRaises(preflight.LockHeldError):
                    with preflight.PreflightLock(lock_file, stale_after_seconds=3600):
                        pass
            self.assertFalse(lock_file.exists())

            lock_file.write_text(json.dumps({"pid": 1, "started_at": "2000-01-01T00:00:00Z"}), encoding="utf-8")
            with preflight.PreflightLock(lock_file, stale_after_seconds=1):
                data = json.loads(lock_file.read_text(encoding="utf-8"))
                self.assertEqual(data["pid"], os.getpid())

    def test_state_round_trip_and_schema_validation(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "state.json"
            state = {"schema_version": 1, "status": "prepared"}
            preflight.write_state(path, state)
            self.assertEqual(preflight.read_state(path), state)
            with self.assertRaises(ValueError):
                preflight.write_state(path, {"schema_version": 2})

    def test_sync_rejects_reparse_target_and_copies_real_directory(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "source"
            target = base / "target"
            source.mkdir()
            target.mkdir()
            (source / "a.md").write_text("alpha", encoding="utf-8")

            with mock.patch.object(preflight, "is_reparse_point", return_value=True):
                with self.assertRaises(preflight.UnsafeReparseTargetError):
                    preflight.sync_real_directory(source, target)

            with mock.patch.object(preflight, "is_reparse_point", return_value=False):
                result = preflight.sync_real_directory(source, target)
            self.assertEqual((target / "a.md").read_text(encoding="utf-8"), "alpha")
            self.assertEqual(result["copied_files"], 1)

    def test_build_index_plan_rules(self):
        current = {"corpus_digest": "abc"}
        previous = {
            "previous_pass_digest": "abc",
            "script_digest": "old",
            "index_plan": {"script_digest": "old"},
        }
        plan = preflight.build_index_plan(current, previous, script_digest="old")
        self.assertEqual(plan["action"], "no_content_change")
        self.assertFalse(plan["requirements"]["codebase_memory"]["required"])
        self.assertFalse(plan["requirements"]["graphify"]["required"])

        plan = preflight.build_index_plan({"corpus_digest": "new"}, previous, script_digest="old")
        self.assertTrue(plan["requirements"]["codebase_memory"]["required"])
        self.assertTrue(plan["requirements"]["graphify"]["required"])

        plan = preflight.build_index_plan(current, previous, script_digest="new")
        self.assertTrue(plan["requirements"]["codegraph"]["required"])

    def test_final_status_and_pass_digest_update(self):
        state = {
            "schema_version": 1,
            "corpus": {"corpus_digest": "digest"},
            "index_plan": {
                "action": "index_required",
                "requirements": {
                    "codebase_memory": {"required": True},
                    "graphify": {"required": True},
                    "codegraph": {"required": True},
                },
            },
            "mcp": {
                "codebase_memory": {"status": "pass"},
                "graphify": {"status": "pass"},
                "codegraph": {"status": "pass"},
            },
        }
        self.assertEqual(preflight.final_status(state), "pass")
        self.assertEqual(preflight.exit_code_for_status("pass"), preflight.EXIT_PASS)
        updated = preflight.apply_final_status(state)
        self.assertEqual(updated["previous_pass_digest"], "digest")

        state["mcp"]["graphify"]["status"] = "fail"
        self.assertEqual(preflight.final_status(state), "blocked")
        self.assertEqual(preflight.exit_code_for_status("blocked"), preflight.EXIT_BLOCKED)

    def test_final_status_required_fail_overrides_pending(self):
        state = {
            "schema_version": 1,
            "corpus": {"corpus_digest": "digest"},
            "index_plan": {
                "action": "index_required",
                "requirements": {
                    "codebase_memory": {"required": True},
                    "graphify": {"required": True},
                    "codegraph": {"required": False},
                },
            },
            "mcp": {
                "codebase_memory": {"status": "fail"},
                "graphify": {"status": "pending"},
            },
        }
        with mock.patch.object(preflight, "_required_mcp_keys", return_value=["graphify", "codebase_memory"]):
            self.assertEqual(preflight.final_status(state), "blocked")
            self.assertIn("final_status: blocked", preflight.render_status(state))

    def test_final_status_invalid_receipts_do_not_pass(self):
        missing_plan = {"schema_version": 1, "corpus": {"corpus_digest": "digest"}, "mcp": {}}
        self.assertEqual(preflight.final_status(missing_plan), "invalid_state")
        self.assertEqual(preflight.exit_code_for_status(preflight.final_status(missing_plan)), preflight.EXIT_INVALID_STATE)

        bad_requirements = {
            "schema_version": 1,
            "corpus": {"corpus_digest": "digest"},
            "index_plan": {"requirements": []},
        }
        self.assertEqual(preflight.final_status(bad_requirements), "invalid_state")

        missing_digest = {"schema_version": 1, "corpus": {}, "index_plan": {"requirements": {}}}
        self.assertEqual(preflight.final_status(missing_digest), "invalid_state")

    def test_final_status_allows_complete_no_content_change_receipt(self):
        state = {
            "schema_version": 1,
            "corpus": {"corpus_digest": "digest"},
            "previous_pass_digest": "digest",
            "index_plan": {
                "action": "no_content_change",
                "requirements": {
                    "codebase_memory": {"required": False},
                    "graphify": {"required": False},
                    "codegraph": {"required": False},
                },
            },
            "mcp": {},
        }
        self.assertEqual(preflight.final_status(state), "pass")

    def test_final_status_rejects_stale_no_content_change_receipt(self):
        state = {
            "schema_version": 1,
            "corpus": {"corpus_digest": "new_digest"},
            "previous_pass_digest": "old_digest",
            "index_plan": {
                "action": "no_content_change",
                "requirements": {
                    "codebase_memory": {"required": False},
                    "graphify": {"required": False},
                    "codegraph": {"required": False},
                },
            },
            "mcp": {},
        }
        self.assertEqual(preflight.final_status(state), "invalid_state")
        self.assertEqual(preflight.exit_code_for_status(preflight.final_status(state)), preflight.EXIT_INVALID_STATE)

    def test_command_builders(self):
        env = preflight.graphify_env()
        self.assertEqual(env["ANTHROPIC_BASE_URL"], "http://127.0.0.1:15721")
        self.assertEqual(env["ANTHROPIC_API_KEY"], "ccswitch-proxy")
        codegraph = preflight.codegraph_command(Path("x"))
        self.assertIn(r"C:\Users\LiN\AppData\Local\codegraph\current\bin\codegraph.cmd", codegraph)
        self.assertIn("index", codegraph)
        self.assertIn("--force", codegraph)
        graphify = preflight.graphify_command(Path("x"))
        self.assertIn(r"C:\Users\LiN\.workbuddy\binaries\python\envs\default\Scripts\graphify.exe", graphify)
        self.assertIn(".", graphify)

    def test_verify_graphify_graph(self):
        graph = {
            "nodes": [
                {"id": "a", "source_file": "articles/a.md", "kind": "Article"},
                {"id": "b", "source_file": "scripts/x.py"},
            ],
            "links": [{"source": "a", "target": "b"}],
            "semantic_hits": 1,
        }
        result = preflight.verify_graphify_graph(graph, graphify_required=True)
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["article_source_files"], 1)

        bad = dict(graph)
        bad["nodes"] = [{"id": "x", "source_file": r"D:\other\external.md"}]
        self.assertEqual(preflight.verify_graphify_graph(bad)["status"], "fail")

        bad = dict(graph)
        bad["nodes"] = [{"id": "x", "source_file": "/tmp/x.md"}]
        self.assertEqual(preflight.verify_graphify_graph(bad)["status"], "fail")

        bad = dict(graph)
        bad["nodes"] = [{"id": "x", "source_file": "articles/../../outside.md"}]
        self.assertEqual(preflight.verify_graphify_graph(bad)["status"], "fail")

        bad = dict(graph)
        bad["semantic_hits"] = 0
        self.assertEqual(preflight.verify_graphify_graph(bad)["status"], "fail")

        bad = dict(graph)
        bad["semantic_hits"] = "n/a"
        result = preflight.verify_graphify_graph(bad)
        self.assertEqual(result["status"], "fail")
        self.assertIn("semantic_hits", " ".join(result["errors"]))

    def test_record_mcp_result_and_render_status(self):
        state = {
            "schema_version": 1,
            "preflight_target": r"D:\Temp\create_skills\bingbingxiaomei-perspective",
            "corpus": {"corpus_digest": "digest"},
            "index_plan": {
                "requirements": {
                    "codebase_memory": {"required": False},
                    "graphify": {"required": False},
                    "codegraph": {"required": False},
                }
            },
            "mcp": {},
        }
        preflight.record_mcp_result(state, "graphify", "pass", {"nodes": 2})
        self.assertEqual(state["mcp"]["graphify"]["status"], "pass")
        preflight.record_mcp_result(state, "codegraph", "deferred")
        self.assertEqual(state["mcp"]["codegraph"]["status"], "deferred")
        with self.assertRaises(ValueError):
            preflight.record_mcp_result(state, "unknown", "pass")
        with self.assertRaises(ValueError):
            preflight.record_mcp_result(state, "graphify", "ok")
        text = preflight.render_status(state)
        self.assertIn("Preflight target: D:/Temp/create_skills/bingbingxiaomei-perspective", text)
        self.assertIn("Status: pass", text)
        self.assertIn("Previous pass: false", text)
        self.assertIn("graphify: pass", text)

        state["previous_pass_digest"] = "digest"
        self.assertIn("Previous pass: true", preflight.render_status(state))

    def test_prepare_resets_required_mcp_results_when_corpus_changes(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            root = base / "target"
            vault = base / "vault"
            articles = preflight.articles_dir(root)
            articles.mkdir(parents=True)
            vault.mkdir()
            (vault / "a.md").write_text("alpha", encoding="utf-8")
            with mock.patch.object(preflight, "DEFAULT_VAULT", vault):
                self.assertEqual(self.call_main(["prepare", "--target", str(root)]), preflight.EXIT_DEFERRED)
            state = preflight.read_state(preflight.state_path(root))
            state["mcp"] = {
                "codebase_memory": {"status": "pass"},
                "graphify": {"status": "pass"},
                "codegraph": {"status": "pass"},
            }
            state["previous_pass_digest"] = state["corpus"]["corpus_digest"]
            preflight.write_state(preflight.state_path(root), state)

            (vault / "b.md").write_text("beta", encoding="utf-8")
            with mock.patch.object(preflight, "DEFAULT_VAULT", vault):
                self.assertEqual(self.call_main(["prepare", "--target", str(root)]), preflight.EXIT_DEFERRED)
            state = preflight.read_state(preflight.state_path(root))

            self.assertTrue(state["index_plan"]["requirements"]["codebase_memory"]["required"])
            self.assertTrue(state["index_plan"]["requirements"]["graphify"]["required"])
            self.assertEqual(state["mcp"]["codebase_memory"]["status"], "pending")
            self.assertEqual(state["mcp"]["graphify"]["status"], "pending")
            self.assertIn("preflight_target", state)

    def test_prepare_syncs_real_articles_from_vault_and_writes_corpus(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            root = base / "target"
            vault = base / "vault"
            articles = preflight.articles_dir(root)
            articles.mkdir(parents=True)
            vault.mkdir()
            (vault / "a.md").write_text("alpha", encoding="utf-8")
            (vault / "nested").mkdir()
            (vault / "nested" / "b.md").write_text("beta", encoding="utf-8")

            with mock.patch.object(preflight, "DEFAULT_VAULT", vault):
                self.assertEqual(self.call_main(["prepare", "--target", str(root)]), preflight.EXIT_DEFERRED)

            state = preflight.read_state(preflight.state_path(root))
            self.assertEqual((articles / "a.md").read_text(encoding="utf-8"), "alpha")
            self.assertEqual((articles / "nested" / "b.md").read_text(encoding="utf-8"), "beta")
            self.assertEqual(state["corpus"]["file_count"], 2)
            self.assertEqual(state["snapshot_status"], "synced")
            self.assertEqual(state["source_before_digest"], state["source_after_digest"])
            self.assertEqual(state["corpus"]["corpus_digest"], preflight.scan_corpus(root)["corpus_digest"])

    def test_prepare_corpus_snapshot_blocks_when_source_changes_during_copy(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            root = base / "target"
            vault = base / "vault"
            articles = preflight.articles_dir(root)
            articles.mkdir(parents=True)
            vault.mkdir()
            (vault / "a.md").write_text("alpha", encoding="utf-8")

            def mutate_source():
                (vault / "a.md").write_text("changed", encoding="utf-8")

            with self.assertRaises(preflight.SnapshotBlockedError) as ctx:
                preflight.prepare_corpus_snapshot(root, vault, after_copy=mutate_source)

            self.assertEqual(ctx.exception.details["snapshot_status"], "blocked")
            self.assertIn("source changed during snapshot", ctx.exception.details["blocked_reason"])

    def test_prepare_corpus_snapshot_blocks_target_only_markdown_in_real_articles(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            root = base / "target"
            vault = base / "vault"
            articles = preflight.articles_dir(root)
            articles.mkdir(parents=True)
            vault.mkdir()
            (vault / "a.md").write_text("alpha", encoding="utf-8")
            (articles / "target_only.md").write_text("local only", encoding="utf-8")

            with self.assertRaises(preflight.SnapshotBlockedError) as ctx:
                preflight.prepare_corpus_snapshot(root, vault)

            details = ctx.exception.details
            self.assertEqual(details["snapshot_status"], "blocked")
            self.assertIn("target-only", details["blocked_reason"])
            self.assertIn("target_only.md", details["target_only_files"])
            self.assertTrue((articles / "target_only.md").exists())

    def test_replace_reparse_with_staging_removes_reparse_itself_without_rmtree(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            reparse_path = base / "articles"
            staging = base / "articles.staging"
            reparse_path.mkdir()
            staging.mkdir()
            (staging / "a.md").write_text("alpha", encoding="utf-8")
            original_rmdir = os.rmdir

            with (
                mock.patch.object(preflight.shutil, "rmtree", side_effect=AssertionError("must not recursively delete reparse target")) as rmtree,
                mock.patch.object(preflight.os, "rmdir", wraps=original_rmdir) as rmdir,
            ):
                preflight._replace_reparse_with_staging(reparse_path, staging)

            rmtree.assert_not_called()
            rmdir.assert_called_once_with(reparse_path)
            self.assertFalse(staging.exists())
            self.assertEqual((reparse_path / "a.md").read_text(encoding="utf-8"), "alpha")

    def test_prepare_corpus_snapshot_reparse_branch_uses_staging_replace_hook(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            root = base / "target"
            vault = base / "vault"
            articles = preflight.articles_dir(root)
            articles.mkdir(parents=True)
            vault.mkdir()
            (articles / "target_only.md").write_text("must not be scanned", encoding="utf-8")
            (vault / "a.md").write_text("alpha", encoding="utf-8")
            calls = []

            def fake_is_reparse(path):
                return Path(path) == articles

            def replace_hook(reparse_path, staging):
                calls.append((Path(reparse_path), Path(staging)))
                self.assertEqual((Path(staging) / "a.md").read_text(encoding="utf-8"), "alpha")
                shutil.rmtree(reparse_path)
                os.replace(staging, reparse_path)

            with mock.patch.object(preflight, "is_reparse_point", side_effect=fake_is_reparse):
                result = preflight.prepare_corpus_snapshot(root, vault, replace_reparse_hook=replace_hook)

            self.assertEqual(result["snapshot_status"], "migrated_reparse")
            self.assertEqual(calls[0][0], articles)
            self.assertEqual((articles / "a.md").read_text(encoding="utf-8"), "alpha")
            self.assertFalse((articles / "target_only.md").exists())

    def test_cli_prepare_status_record_finalize(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            root = base / "target"
            vault = base / "vault"
            preflight.articles_dir(root).mkdir(parents=True)
            vault.mkdir()
            (vault / "a.md").write_text("alpha", encoding="utf-8")

            with mock.patch.object(preflight, "DEFAULT_VAULT", vault):
                self.assertEqual(self.call_main(["prepare", "--target", str(root)]), preflight.EXIT_DEFERRED)
            state = preflight.read_state(preflight.state_path(root))
            self.assertEqual(state["schema_version"], 1)
            self.assertEqual(state["preflight_target"], str(root))
            self.assertIn("index_plan", state)
            self.assertEqual(self.call_main(["status", "--target", str(root)]), preflight.EXIT_DEFERRED)
            self.assertEqual(
                self.call_main(["record-mcp", "codebase_memory", "pass", "--target", str(root)]),
                preflight.EXIT_DEFERRED,
            )
            self.assertEqual(
                self.call_main(["record-mcp", "graphify", "pass", "--target", str(root)]),
                preflight.EXIT_PASS,
            )
            self.assertEqual(
                self.call_main(["record-mcp", "codegraph", "pass", "--target", str(root)]),
                preflight.EXIT_PASS,
            )
            self.assertEqual(self.call_main(["finalize", "--target", str(root)]), preflight.EXIT_PASS)
            state = preflight.read_state(preflight.state_path(root))
            self.assertEqual(state["previous_pass_digest"], state["corpus"]["corpus_digest"])


if __name__ == "__main__":
    unittest.main()
