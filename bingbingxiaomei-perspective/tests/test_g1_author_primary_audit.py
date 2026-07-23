import importlib.util
import hashlib
import json
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = PROJECT_ROOT / "scripts" / "audit_g1_author_primary.py"


def load_audit_module():
    if not MODULE_PATH.exists():
        raise AssertionError(f"missing G1a audit script: {MODULE_PATH}")
    spec = importlib.util.spec_from_file_location(
        "audit_g1_author_primary",
        MODULE_PATH,
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class G1AuthorPrimaryAuditTests(unittest.TestCase):
    def test_quote_matching_distinguishes_exact_and_paraphrase(self):
        module = load_audit_module()
        source = "清仓。扩张还没有投产，按投产的盈利，市值先到了。"
        self.assertEqual(
            module.match_quote("清仓", source),
            "exact",
        )
        self.assertEqual(
            module.match_quote("按投产的盈利，市值先到了。清仓", source),
            "paraphrase_supported",
        )

    def test_phase_two_evidence_is_resolved_to_author_primary(self):
        module = load_audit_module()
        report = module.build_audit_report(PROJECT_ROOT)
        self.assertGreaterEqual(report["evidence_reference_count"], 59)
        self.assertEqual(report["audited_source_file_count"], 6)
        self.assertEqual(report["unresolved_reference_count"], 0)
        self.assertEqual(report["non_author_reference_count"], 0)
        self.assertEqual(report["contextual_non_author_reference_count"], 1)
        self.assertEqual(report["candidate_model_count"], 7)
        self.assertEqual(report["candidate_heuristic_count"], 9)

    def test_g1a_receipt_matches_generated_artifacts(self):
        receipt_path = (
            PROJECT_ROOT
            / "references"
            / "research"
            / "g1-local"
            / "g1a-receipt.json"
        )
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        self.assertEqual(receipt["status"], "passed_for_G1a_only")
        self.assertEqual(receipt["next_gate"], "G1b")
        self.assertEqual(receipt["article_count"], 520)
        self.assertEqual(receipt["role_manifest"]["role_counts"]["unknown"], 0)
        self.assertEqual(
            len(receipt["revalidated_candidates"]["candidate_models"]),
            7,
        )
        self.assertEqual(
            len(receipt["revalidated_candidates"]["candidate_heuristics"]),
            9,
        )

        for section in (
            "role_manifest",
            "overrides",
            "author_primary_audit",
            "revalidated_candidates",
        ):
            artifact = PROJECT_ROOT / receipt[section]["path"]
            actual_digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
            self.assertEqual(
                receipt[section]["sha256"],
                actual_digest,
                f"stale digest for {section}",
            )


if __name__ == "__main__":
    unittest.main()
