import importlib.util
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = PROJECT_ROOT / "scripts" / "build_article_role_manifest.py"
ARTICLE_RELATIVE_PATH = (
    "references/sources/articles/"
    "2026-06-20 102347_冰冰小美_中美战略实施加速的转折点.md"
)
ARTICLE_PATH = PROJECT_ROOT / ARTICLE_RELATIVE_PATH
NESTED_REPLY_RELATIVE_PATH = (
    "references/sources/articles/"
    "2025-09-15 164718_冰冰小美_世纪华通 ，也就是st华通。"
    "A股游戏第一股。这个个股很好的诠释了A股的生态。为啥？"
    "世纪华通是高毅资本冯柳挖掘并且重仓的。.md"
)
NESTED_REPLY_PATH = PROJECT_ROOT / NESTED_REPLY_RELATIVE_PATH
ARTICLES_DIR = PROJECT_ROOT / "references" / "sources" / "articles"
OVERRIDES_PATH = (
    PROJECT_ROOT
    / "references"
    / "research"
    / "article-content-role-overrides.json"
)


def load_role_manifest_module():
    if not MODULE_PATH.exists():
        raise AssertionError(f"missing role manifest generator: {MODULE_PATH}")
    spec = importlib.util.spec_from_file_location(
        "build_article_role_manifest",
        MODULE_PATH,
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ArticleRoleManifestTests(unittest.TestCase):
    def setUp(self):
        self.module = load_role_manifest_module()
        self.overrides = [
            {
                "article_path": ARTICLE_RELATIVE_PATH,
                "start_line": 69,
                "end_line": 150,
                "role": "secondary_analysis",
                "reason": "第三方用户发布的系统性文章解读",
            }
        ]
        self.segments = self.module.parse_article(
            ARTICLE_PATH,
            ARTICLE_RELATIVE_PATH,
            self.overrides,
        )

    def segment_for_line(self, line_number):
        matches = [
            segment
            for segment in self.segments
            if segment["start_line"] <= line_number <= segment["end_line"]
        ]
        self.assertEqual(
            len(matches),
            1,
            f"line {line_number} should belong to exactly one segment",
        )
        return matches[0]

    def test_real_article_separates_author_and_third_party_content(self):
        for line_number in (16, 18, 34):
            segment = self.segment_for_line(line_number)
            self.assertEqual(segment["role"], "author_post")
            self.assertEqual(
                segment["evidence_eligibility"],
                "author_primary",
            )

        for line_number in (39, 41, 46, 50, 62):
            segment = self.segment_for_line(line_number)
            self.assertEqual(segment["role"], "author_reply")
            self.assertEqual(
                segment["evidence_eligibility"],
                "author_primary",
            )

        comment_header = self.segment_for_line(67)
        self.assertEqual(comment_header["speaker_uid"], "6310331350")
        self.assertEqual(comment_header["role"], "third_party_comment")
        self.assertEqual(
            comment_header["evidence_eligibility"],
            "context_only",
        )

        analysis = self.segment_for_line(69)
        self.assertEqual(analysis["role"], "secondary_analysis")
        self.assertEqual(analysis["classification_source"], "reviewed_override")
        self.assertEqual(analysis["evidence_eligibility"], "excluded")

    def test_segments_do_not_overlap(self):
        ordered = sorted(
            self.segments,
            key=lambda segment: (
                segment["start_line"],
                segment["end_line"],
            ),
        )
        for previous, current in zip(ordered, ordered[1:]):
            self.assertLess(previous["end_line"], current["start_line"])

    def test_blockquoted_author_reply_is_not_kept_in_third_party_segment(self):
        segments = self.module.parse_article(
            NESTED_REPLY_PATH,
            NESTED_REPLY_RELATIVE_PATH,
            [],
        )

        def segment_for(line_number):
            matches = [
                segment
                for segment in segments
                if segment["start_line"] <= line_number <= segment["end_line"]
            ]
            self.assertEqual(len(matches), 1)
            return matches[0]

        self.assertEqual(segment_for(30)["role"], "third_party_comment")
        self.assertEqual(segment_for(32)["role"], "third_party_comment")
        self.assertEqual(segment_for(33)["role"], "author_reply")
        self.assertEqual(segment_for(35)["role"], "author_reply")
        self.assertEqual(
            segment_for(35)["evidence_eligibility"],
            "author_primary",
        )

    def test_only_author_roles_are_primary_evidence(self):
        for segment in self.segments:
            if segment["evidence_eligibility"] == "author_primary":
                self.assertIn(
                    segment["role"],
                    {"author_post", "author_reply"},
                )
            if segment["role"] in {
                "third_party_comment",
                "secondary_analysis",
                "unknown",
            }:
                self.assertNotEqual(
                    segment["evidence_eligibility"],
                    "author_primary",
                )

    def test_segment_ids_and_text_digests_are_stable(self):
        repeated = self.module.parse_article(
            ARTICLE_PATH,
            ARTICLE_RELATIVE_PATH,
            self.overrides,
        )
        self.assertEqual(
            [segment["segment_id"] for segment in self.segments],
            [segment["segment_id"] for segment in repeated],
        )
        self.assertTrue(
            all(len(segment["text_digest"]) == 64 for segment in self.segments)
        )

    def test_full_corpus_has_complete_non_overlapping_body_coverage(self):
        manifest = self.module.build_manifest(
            ARTICLES_DIR,
            self.module.load_overrides(OVERRIDES_PATH),
        )
        stats = self.module.manifest_stats(manifest)
        self.assertEqual(stats["article_count"], 520)
        self.assertEqual(stats["unknown_segment_count"], 0)

        by_article = {}
        for segment in manifest:
            by_article.setdefault(segment["article_path"], []).append(segment)
            if segment["evidence_eligibility"] == "author_primary":
                self.assertIn(
                    segment["role"],
                    {"author_post", "author_reply"},
                )

        for relative_path, segments in by_article.items():
            ordered = sorted(segments, key=lambda item: item["start_line"])
            article_path = PROJECT_ROOT / relative_path
            article_lines = article_path.read_text(
                encoding="utf-8"
            ).splitlines()
            for previous, current in zip(ordered, ordered[1:]):
                uncovered = article_lines[
                    previous["end_line"] : current["start_line"] - 1
                ]
                self.assertTrue(
                    all(not line.strip() for line in uncovered),
                    f"non-empty gap in {relative_path}",
                )
            trailing = article_lines[ordered[-1]["end_line"] :]
            self.assertTrue(
                all(not line.strip() for line in trailing),
                f"trailing non-empty body content is uncovered in {relative_path}",
            )


if __name__ == "__main__":
    unittest.main()
