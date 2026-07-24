import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CLASSIFIER_PATH = PROJECT_ROOT / "scripts" / "classify-articles.py"
ANALYZER_PATH = PROJECT_ROOT / "scripts" / "analyze_classification.py"
TAXONOMY_PATH = PROJECT_ROOT / "references" / "taxonomy.json"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ClassificationPipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.classifier = load_module("article_classifier", CLASSIFIER_PATH)
        cls.analyzer = load_module("classification_analyzer", ANALYZER_PATH)
        cls.taxonomy, cls.taxonomy_digest = cls.classifier.load_taxonomy(
            TAXONOMY_PATH
        )
        cls.model_routes, cls.heuristic_routes = (
            cls.classifier.build_routing_index(cls.taxonomy)
        )

    def article(self, content):
        return {
            "date": "2026-07-24",
            "time": "120000",
            "title": "测试文章",
            "fname": "2026-07-24 120000_冰冰小美_测试文章.md",
            "content": content,
            "len": len(content),
        }

    def test_taxonomy_drives_current_ids_without_legacy_model_ids(self):
        self.assertEqual(
            set(self.model_routes),
            {f"m{i:02d}" for i in range(1, 7)},
        )
        self.assertEqual(
            set(self.heuristic_routes),
            {f"h{i:02d}" for i in range(1, 10)},
        )
        self.assertFalse(
            any(model_id.startswith("model_") for model_id in self.model_routes)
        )
        for model in self.taxonomy["models"]:
            self.assertEqual(
                set(self.model_routes[model["id"]]["terms"]),
                set(model["routing_terms"]),
            )
        for heuristic in self.taxonomy["heuristics"]:
            self.assertEqual(
                set(self.heuristic_routes[heuristic["id"]]["terms"]),
                set(heuristic["routing_terms"]),
            )

    def test_explicit_routing_terms_cover_non_m01_models(self):
        cases = {
            "m02": "风险演绎进入时间窗口，等待关键节点确认。",
            "m03": "国家竞争要求独立自主全产业链与产业安全。",
            "m04": "订单、产能和盈利兑现共同验证产业链地位。",
            "m05": "回读官方原文、财报和研报再交叉印证。",
            "m06": "风险预算必须匹配睡眠、承受力和仓位。",
        }
        for expected_model, content in cases.items():
            with self.subTest(expected_model=expected_model):
                result = self.classifier.classify_article(
                    self.article(content),
                    self.model_routes,
                    self.heuristic_routes,
                )
                self.assertEqual(
                    result["primary_model_id"],
                    expected_model,
                )
                self.assertFalse(result["unresolved"])

    def test_multiple_primary_text_hits_produce_traceable_model_candidate(self):
        result = self.classifier.classify_article(
            self.article("三要素需要同时观察流动性、情绪位置与竞争格局。"),
            self.model_routes,
            self.heuristic_routes,
        )

        self.assertEqual(result["primary_model_id"], "m01")
        self.assertFalse(result["unresolved"])
        self.assertGreaterEqual(result["confidence"], 0.65)
        self.assertTrue(result["evidence_snippets"])
        self.assertIn("matched_terms", result["evidence_snippets"][0])

    def test_single_weak_hit_remains_unresolved(self):
        result = self.classifier.classify_article(
            self.article("这里只提到一次三要素。"),
            self.model_routes,
            self.heuristic_routes,
        )

        self.assertIsNone(result["primary_model_id"])
        self.assertTrue(result["unresolved"])
        self.assertLess(result["confidence"], 0.65)
        self.assertEqual(result["model_candidates"][0]["id"], "m01")

    def test_tied_candidates_remain_low_confidence_and_unresolved(self):
        routes = {
            "m01": {
                "name": "one",
                "status": "confirmed",
                "terms": ["共同", "甲项"],
            },
            "m02": {
                "name": "two",
                "status": "confirmed",
                "terms": ["共同", "乙项"],
            },
        }
        result = self.classifier.classify_article(
            self.article("共同证据同时包含甲项和乙项。"),
            routes,
            {},
        )

        self.assertIsNone(result["primary_model_id"])
        self.assertTrue(result["unresolved"])
        self.assertLess(result["confidence"], 0.65)

    def test_current_output_contains_required_contract_and_digests(self):
        result = self.classifier.classify_article(
            self.article("三要素同时观察流动性、情绪位置与竞争格局。"),
            self.model_routes,
            self.heuristic_routes,
        )
        output = self.classifier.build_output(
            [result],
            self.taxonomy,
            self.taxonomy_digest,
            corpus_digest="corpus-digest",
            timestamp="2026-07-24T120000",
        )

        self.assertEqual(output["schema_version"], 2)
        self.assertEqual(output["corpus_digest"], "corpus-digest")
        self.assertEqual(output["taxonomy_digest"], self.taxonomy_digest)
        self.assertEqual(output["per_article"][0]["primary_model_id"], "m01")
        self.assertIn("candidate_heuristics", output["per_article"][0])
        self.assertIn("evidence_snippets", output["per_article"][0])
        self.assertNotIn("top_models", output["per_article"][0])

    def test_analyzer_reads_current_pointer_and_validates_current_ids(self):
        current_data = {
            "schema_version": 2,
            "taxonomy_digest": self.taxonomy_digest,
            "corpus_digest": "corpus-digest",
            "per_article": [
                {
                    "article": "current",
                    "primary_model_id": "m01",
                    "candidate_heuristics": [{"id": "h02", "score": 2}],
                    "confidence": 0.8,
                    "unresolved": False,
                }
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            artifact = tmp_path / "classification.json"
            pointer = tmp_path / "current.json"
            artifact.write_text(
                json.dumps(current_data, ensure_ascii=False),
                encoding="utf-8",
            )
            pointer.write_text(
                json.dumps({"path": artifact.name}),
                encoding="utf-8",
            )

            resolved = self.analyzer.resolve_input_path(None, pointer)
            summary = self.analyzer.analyze_file(resolved, TAXONOMY_PATH)

        self.assertEqual(summary["mode"], "current")
        self.assertEqual(summary["model_counts"], {"m01": 1})
        self.assertEqual(summary["unresolved_count"], 0)

    def test_analyzer_accepts_explicit_legacy_file_as_read_only_history(self):
        legacy_data = {
            "per_article": [
                {
                    "article": "legacy",
                    "top_models": [
                        ["model_9_ai_reform", "AI改造投资本身", 1.0]
                    ],
                    "top_heuristics": [],
                }
            ]
        }
        with tempfile.TemporaryDirectory() as tmp:
            legacy_path = Path(tmp) / "legacy.json"
            legacy_path.write_text(
                json.dumps(legacy_data, ensure_ascii=False),
                encoding="utf-8",
            )
            summary = self.analyzer.analyze_file(
                legacy_path,
                TAXONOMY_PATH,
            )

        self.assertEqual(summary["mode"], "legacy")
        self.assertEqual(summary["model_counts"], {"model_9_ai_reform": 1})

    def test_analyzer_rejects_legacy_ids_in_current_schema(self):
        invalid_current = {
            "schema_version": 2,
            "taxonomy_digest": self.taxonomy_digest,
            "corpus_digest": "corpus-digest",
            "per_article": [
                {
                    "article": "invalid",
                    "primary_model_id": "model_1_three_elements",
                    "candidate_heuristics": [],
                    "confidence": 0.9,
                    "unresolved": False,
                }
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "invalid-current.json"
            path.write_text(
                json.dumps(invalid_current, ensure_ascii=False),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "unknown current model"):
                self.analyzer.analyze_file(path, TAXONOMY_PATH)

    def test_analyzer_rejects_stale_taxonomy_digest(self):
        stale_current = {
            "schema_version": 2,
            "taxonomy_digest": "stale-taxonomy",
            "corpus_digest": "corpus-digest",
            "per_article": [],
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "stale-current.json"
            path.write_text(
                json.dumps(stale_current, ensure_ascii=False),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "taxonomy digest mismatch"):
                self.analyzer.analyze_file(path, TAXONOMY_PATH)


if __name__ == "__main__":
    unittest.main()
