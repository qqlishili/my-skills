import json
import re
import unittest
from pathlib import Path

from scripts.validate_article_interpretation import validate_article_brief


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = (
    PROJECT_ROOT / "references" / "schemas" / "article-interpretation.schema.json"
)
TEMPLATE_PATH = (
    PROJECT_ROOT / "references" / "templates" / "article-interpretation.md"
)
TAXONOMY_PATH = PROJECT_ROOT / "references" / "taxonomy.json"
ACTIVE_FILES = [
    PROJECT_ROOT / "SKILL.md",
    PROJECT_ROOT / "SKILL.core.md",
    PROJECT_ROOT / "docs" / "maintenance.md",
    PROJECT_ROOT / "test-prompts.json",
    PROJECT_ROOT / "references" / "templates" / "standard-stock-report.md",
    PROJECT_ROOT / "references" / "templates" / "deep-stock-report.md",
]
CORPUS_BOUNDARY_FILES = ACTIVE_FILES + [
    PROJECT_ROOT / "references" / "research" / "06-timeline.md",
]


class ArticleInterpretationContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        cls.template = TEMPLATE_PATH.read_text(encoding="utf-8")
        cls.taxonomy = json.loads(TAXONOMY_PATH.read_text(encoding="utf-8"))

    def make_valid_brief(self):
        return {
            "schema_version": 1,
            "input": {
                "schema_version": 1,
                "input_mode": "ephemeral",
                "article_text": "用户分析：方向长期不变。",
            },
            "input_summary": "用户对历史框架的二次分析。",
            "document_type": "secondary_analysis",
            "input_segments": [
                {
                    "segment_id": "s01",
                    "role": "analyst_text",
                    "line_span": {"start_line": 1, "end_line": 1},
                    "text": "用户分析：方向长期不变。",
                }
            ],
            "claim_results": [
                {
                    "claim": {
                        "claim_id": "c01",
                        "input_segment_id": "s01",
                        "input_segment_role": "analyst_text",
                        "source_span": {
                            "start_line": 1,
                            "end_line": 1,
                            "quote": "方向长期不变",
                        },
                        "claim_type": "analyst_inference",
                        "normalized_concept": "长期方向",
                        "statement": "分析者认为长期方向未变。",
                        "confidence": 0.7,
                    },
                    "historical_relation": {
                        "relation": "no_evidence",
                        "historical_evidence": [],
                        "reasoning": "当前语料未找到作者一级证据。",
                        "confidence": 0.2,
                    },
                }
            ],
            "taxonomy_mapping": {
                "status": "mapped",
                "model_ids": ["m03"],
                "heuristic_ids": [],
                "reasoning": "仅作为分析者推断映射。",
            },
            "supporting_evidence": [],
            "counter_evidence": [],
            "unknowns": [],
            "honesty_boundaries": ["当前 520 篇语料内无证据。"],
        }

    def test_ephemeral_input_and_document_role_contract(self):
        input_schema = self.schema["$defs"]["input"]
        self.assertEqual(input_schema["required"], [
            "schema_version",
            "input_mode",
            "article_text",
        ])
        self.assertEqual(
            input_schema["properties"]["input_mode"]["const"],
            "ephemeral",
        )
        segment = self.schema["$defs"]["input_segment"]
        self.assertEqual(
            set(segment["properties"]["role"]["enum"]),
            {"quoted_source", "analyst_text", "external_context", "unknown"},
        )
        brief = self.schema["$defs"]["brief"]
        self.assertEqual(
            set(brief["properties"]["document_type"]["enum"]),
            {"primary_article", "secondary_analysis", "mixed", "unknown"},
        )

    def test_claim_and_relation_enums_are_closed(self):
        claim = self.schema["$defs"]["claim"]
        self.assertEqual(
            set(claim["properties"]["claim_type"]["enum"]),
            {
                "author_quote",
                "author_judgement",
                "analyst_inference",
                "external_fact",
            },
        )
        brief = self.schema["$defs"]["brief"]
        self.assertIn("claim_results", brief["required"])
        self.assertNotIn("claims", brief["properties"])
        self.assertNotIn("historical_relations", brief["properties"])
        relation = self.schema["$defs"]["historical_relation"]
        self.assertEqual(
            set(relation["properties"]["relation"]["enum"]),
            {
                "repeats",
                "extends",
                "narrows",
                "revises",
                "contradicts",
                "applies",
                "no_evidence",
            },
        )

    def test_primary_evidence_contract_excludes_derived_sources(self):
        evidence = self.schema["$defs"]["historical_evidence"]
        self.assertEqual(
            set(evidence["properties"]["role"]["enum"]),
            {"author_post", "author_reply"},
        )
        self.assertEqual(
            evidence["properties"]["evidence_eligibility"]["const"],
            "author_primary",
        )
        self.assertEqual(
            evidence["properties"]["verified_against_primary_text"]["const"],
            True,
        )
        self.assertIn("no_evidence", json.dumps(self.schema, ensure_ascii=False))
        for forbidden in (
            "third_party_comment",
            "secondary_analysis",
            "research summary as evidence",
            "graph edge as evidence",
        ):
            self.assertIn(forbidden, self.template)

    def test_taxonomy_mapping_uses_current_ids(self):
        mapping = self.schema["$defs"]["taxonomy_mapping"]
        schema_models = set(
            mapping["properties"]["model_ids"]["items"]["enum"]
        )
        schema_heuristics = set(
            mapping["properties"]["heuristic_ids"]["items"]["enum"]
        )
        self.assertEqual(schema_models, {item["id"] for item in self.taxonomy["models"]})
        self.assertEqual(
            schema_heuristics,
            {item["id"] for item in self.taxonomy["heuristics"]},
        )

    def test_template_routes_article_brief_away_from_stock_reports(self):
        required_phrases = [
            "input_mode=ephemeral",
            "不写入 520 篇 corpus",
            "author_primary",
            "no_evidence",
            "verified_against_primary_text=true",
            "文章解释简报",
            "与股票报告路由互斥",
        ]
        for phrase in required_phrases:
            self.assertIn(phrase, self.template)

    def test_active_entrypoints_remove_legacy_taxonomy_and_fix_boundaries(self):
        combined = "\n".join(path.read_text(encoding="utf-8") for path in ACTIVE_FILES)
        for pattern in (
            r"v1\.7 运行层",
            r"运行层 \+ 证据层",
            r"deep-9",
            r"模型9",
            r"模型1-8",
            r"运行模型\s*[1-9]",
            r"模型\s*[1-9](?:\+\d+)?",
            r"启发式\s*1[4-7]",
            r"启发式\s*(?:1[0-9]|[1-9])",
            r"7\s*运行模型",
            r"17\s*启发式",
            r"2025年文章未保存",
            r"2025年文章缺失",
            r"articles[^\n]{0,30}符号链接",
        ):
            self.assertIsNone(re.search(pattern, combined))
        for phrase in (
            "2025 年本地有 68 篇",
            "520 篇雪球专栏语料",
            "真实目录",
            "不覆盖作者全部公开表达",
        ):
            self.assertIn(phrase, combined)

    def test_active_corpus_boundaries_do_not_restore_the_2025_gap(self):
        combined = "\n".join(
            path.read_text(encoding="utf-8") for path in CORPUS_BOUNDARY_FILES
        )
        for pattern in (
            r"\|\s*2025\s*\|\s*\*\*0\*\*",
            r"2025\s*年?文章未(?:被)?收录",
            r"大量\s*2025\s*年文章未(?:被)?收录",
        ):
            self.assertIsNone(re.search(pattern, combined))
        self.assertIn("2025 年 68 篇", combined)

    def test_stock_templates_read_current_taxonomy(self):
        model_ids = {item["id"] for item in self.taxonomy["models"]}
        heuristic_ids = {item["id"] for item in self.taxonomy["heuristics"]}
        for name in ("standard-stock-report.md", "deep-stock-report.md"):
            text = (PROJECT_ROOT / "references" / "templates" / name).read_text(
                encoding="utf-8"
            )
            self.assertIn("references/taxonomy.json", text)
            for model_id in ("m01", "m02", "m03", "m04", "m05", "m06"):
                self.assertIn(model_id, text)
            self.assertTrue(set(re.findall(r"\bm\d{2}\b", text)) <= model_ids)
            self.assertTrue(set(re.findall(r"\bh\d{2}\b", text)) <= heuristic_ids)
            self.assertIsNone(re.search(r"(?:模型|启发式)\s*(?:1[0-9]|[1-9])", text))
            self.assertNotIn("7运行模型", text)
            self.assertNotIn("17启发式", text)

    def test_valid_brief_passes_semantic_validation(self):
        validate_article_brief(self.make_valid_brief())

    def test_secondary_analysis_cannot_be_author_judgement(self):
        brief = self.make_valid_brief()
        brief["claim_results"][0]["claim"]["claim_type"] = "author_judgement"
        with self.assertRaisesRegex(ValueError, "misattributed|non-primary"):
            validate_article_brief(brief)

    def test_every_claim_result_requires_a_relation_result(self):
        brief = self.make_valid_brief()
        brief["claim_results"][0].pop("historical_relation")
        with self.assertRaisesRegex(ValueError, "invalid relation"):
            validate_article_brief(brief)

    def test_semantic_validator_checks_ids_spans_paths_and_unavailable_mapping(self):
        brief = self.make_valid_brief()
        brief["input_segments"][0]["line_span"] = {"start_line": 2, "end_line": 1}
        with self.assertRaisesRegex(ValueError, "invalid end_line"):
            validate_article_brief(brief)

        brief = self.make_valid_brief()
        brief["taxonomy_mapping"] = {
            "status": "unavailable_before_G2",
            "model_ids": ["m01"],
            "heuristic_ids": [],
            "reasoning": "G2 尚未通过。",
        }
        with self.assertRaisesRegex(ValueError, "unavailable mapping contains model IDs"):
            validate_article_brief(brief)

        brief = self.make_valid_brief()
        evidence = {
            "article_path": "references/sources/articles/../research/fake.md",
            "segment_id": "seg",
            "role": "author_post",
            "evidence_eligibility": "author_primary",
            "line_span": {"start_line": 1, "end_line": 1},
            "quote": "伪造路径",
            "retrieval_method": "exact",
            "verified_against_primary_text": True,
        }
        relation = brief["claim_results"][0]["historical_relation"]
        relation["relation"] = "repeats"
        relation["historical_evidence"] = [evidence]
        with self.assertRaisesRegex(ValueError, "invalid article_path"):
            validate_article_brief(brief)

    def test_semantic_validator_rejects_duplicate_or_dangling_references(self):
        brief = self.make_valid_brief()
        brief["input_segments"].append(dict(brief["input_segments"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate segment_id"):
            validate_article_brief(brief)

        brief = self.make_valid_brief()
        duplicate = json.loads(json.dumps(brief["claim_results"][0]))
        brief["claim_results"].append(duplicate)
        with self.assertRaisesRegex(ValueError, "duplicate claim_id"):
            validate_article_brief(brief)

        brief = self.make_valid_brief()
        brief["claim_results"][0]["claim"]["input_segment_id"] = "s99"
        with self.assertRaisesRegex(ValueError, "unknown input_segment_id"):
            validate_article_brief(brief)

        brief = self.make_valid_brief()
        brief["claim_results"][0]["claim"]["input_segment_role"] = "quoted_source"
        with self.assertRaisesRegex(ValueError, "input segment role mismatch"):
            validate_article_brief(brief)

    def test_semantic_validator_rejects_non_primary_historical_evidence(self):
        brief = self.make_valid_brief()
        relation = brief["claim_results"][0]["historical_relation"]
        relation["relation"] = "repeats"
        relation["historical_evidence"] = [
            {
                "article_path": "references/sources/articles/example.md",
                "segment_id": "seg",
                "role": "third_party_comment",
                "evidence_eligibility": "context_only",
                "line_span": {"start_line": 1, "end_line": 1},
                "quote": "第三方解读",
                "retrieval_method": "graph_candidate",
                "verified_against_primary_text": False,
            }
        ]
        with self.assertRaisesRegex(ValueError, "non-author role"):
            validate_article_brief(brief)

    def test_prompts_cover_new_article_and_boundary_routes(self):
        prompts = json.loads((PROJECT_ROOT / "test-prompts.json").read_text(
            encoding="utf-8"
        ))
        tags = {tag for item in prompts for tag in item.get("tags", [])}
        self.assertTrue({
            "secondary_analysis",
            "primary_article",
            "no_evidence",
            "contradicts",
            "stock_route",
            "corpus_2025",
            "non_column_boundary",
            "low_confidence",
            "framework_only",
        } <= tags)


if __name__ == "__main__":
    unittest.main()
