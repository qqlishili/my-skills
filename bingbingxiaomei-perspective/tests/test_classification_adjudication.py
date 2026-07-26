import importlib.util
import hashlib
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ADJUDICATOR_PATH = PROJECT_ROOT / "scripts" / "adjudicate_classification.py"
TAXONOMY_PATH = PROJECT_ROOT / "references" / "taxonomy.json"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ClassificationAdjudicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.adjudicator = load_module("classification_adjudicator", ADJUDICATOR_PATH)
        cls.taxonomy = cls.adjudicator.load_json(TAXONOMY_PATH)
        cls.taxonomy_digest = hashlib.sha256(
            TAXONOMY_PATH.read_bytes()
        ).hexdigest()

    def raw_output(self):
        return {
            "schema_version": 2,
            "timestamp": "2026-07-26T120000",
            "corpus_digest": self.taxonomy["corpus_digest"],
            "taxonomy_digest": self.taxonomy_digest,
            "taxonomy_schema_version": 1,
            "taxonomy_ids": {
                "models": [item["id"] for item in self.taxonomy["models"]],
                "heuristics": [item["id"] for item in self.taxonomy["heuristics"]],
            },
            "total_articles": 3,
            "unresolved_count": 2,
            "per_article": [
                {
                    "fname": "a.md",
                    "primary_model_id": "m01",
                    "candidate_heuristics": [],
                    "confidence": 0.8,
                    "unresolved": False,
                },
                {
                    "fname": "b.md",
                    "primary_model_id": None,
                    "candidate_heuristics": [{"id": "h04", "score": 1}],
                    "confidence": 0.35,
                    "unresolved": True,
                },
                {
                    "fname": "c.md",
                    "primary_model_id": None,
                    "candidate_heuristics": [],
                    "confidence": 0.0,
                    "unresolved": True,
                },
            ],
        }

    def test_adjudication_preserves_classifier_values_and_applies_decisions(self):
        manual_review = {
            "entries": [
                {
                    "fname": "a.md",
                    "model_verdict": "incorrect",
                    "expected_model_id": "m02",
                    "supported_heuristic_ids": [],
                    "notes": "m02 dominates",
                }
            ]
        }
        batch_entries = [
            {
                "fname": "b.md",
                "model_verdict": "resolved_to_model",
                "expected_primary_model_id": "m03",
                "secondary_model_ids": [],
                "supported_heuristic_ids": ["h04"],
                "confidence": "high",
                "evidence_summary": "evidence",
                "rationale": "m03 dominates",
            },
            {
                "fname": "c.md",
                "model_verdict": "remains_unresolved",
                "expected_primary_model_id": None,
                "secondary_model_ids": ["m01", "m02"],
                "supported_heuristic_ids": [],
                "confidence": "low",
                "evidence_summary": "mixed evidence",
                "rationale": "no dominant model",
            },
        ]

        output = self.adjudicator.adjudicate_output(
            self.raw_output(),
            manual_review,
            batch_entries,
            self.taxonomy,
            self.taxonomy_digest,
            timestamp="2026-07-26T130000",
        )

        by_name = {item["fname"]: item for item in output["per_article"]}
        self.assertEqual(by_name["a.md"]["classifier_primary_model_id"], "m01")
        self.assertEqual(by_name["a.md"]["primary_model_id"], "m02")
        self.assertEqual(by_name["b.md"]["primary_model_id"], "m03")
        self.assertEqual(by_name["b.md"]["verified_heuristic_ids"], ["h04"])
        self.assertIsNone(by_name["c.md"]["primary_model_id"])
        self.assertTrue(by_name["c.md"]["unresolved"])
        self.assertEqual(output["unresolved_count"], 1)
        self.assertEqual(output["adjudication"]["reviewed_total"], 3)

    def test_batch_validation_rejects_missing_or_duplicate_unresolved_files(self):
        expected = {"b.md", "c.md"}
        duplicate = [
            {"fname": "b.md"},
            {"fname": "b.md"},
        ]
        with self.assertRaisesRegex(ValueError, "duplicate review filename"):
            self.adjudicator.validate_review_coverage(expected, duplicate)

        with self.assertRaisesRegex(ValueError, "review coverage mismatch"):
            self.adjudicator.validate_review_coverage(expected, [{"fname": "b.md"}])

    def test_adjudication_rejects_an_already_adjudicated_artifact(self):
        raw = self.raw_output()
        raw["classification_stage"] = "adjudicated"
        raw["per_article"][0]["classifier_primary_model_id"] = "m01"

        with self.assertRaisesRegex(ValueError, "raw classification artifact"):
            self.adjudicator.adjudicate_output(
                raw,
                {"entries": []},
                [],
                self.taxonomy,
                self.taxonomy_digest,
            )

    def test_batch_validation_rejects_invalid_confidence(self):
        entry = {
            "fname": "b.md",
            "model_verdict": "remains_unresolved",
            "expected_primary_model_id": None,
            "secondary_model_ids": [],
            "supported_heuristic_ids": [],
            "confidence": 0.8,
        }

        with self.assertRaisesRegex(ValueError, "invalid review confidence"):
            self.adjudicator._validate_ids(
                entry,
                {"m01"},
                set(),
                batch_entry=True,
            )

    def test_adjudication_rejects_noncanonical_raw_digests(self):
        raw = self.raw_output()
        raw["corpus_digest"] = "noncanonical"
        with self.assertRaisesRegex(ValueError, "corpus digest mismatch"):
            self.adjudicator.adjudicate_output(
                raw,
                {"entries": []},
                [],
                self.taxonomy,
                self.taxonomy_digest,
            )

    def test_adjudication_rejects_duplicate_manual_reviews(self):
        entry = {
            "fname": "a.md",
            "model_verdict": "verified",
            "expected_model_id": "m01",
            "supported_heuristic_ids": [],
            "notes": "duplicate",
        }
        with self.assertRaisesRegex(ValueError, "duplicate review filename"):
            self.adjudicator.adjudicate_output(
                self.raw_output(),
                {"entries": [entry, dict(entry)]},
                [],
                self.taxonomy,
                self.taxonomy_digest,
            )

    def test_batch_metadata_requires_contiguous_exact_ranges(self):
        batches = [
            {
                "schema_version": 1,
                "batch_id": "01",
                "unresolved_sorted_range": {
                    "start_inclusive": 0,
                    "end_exclusive": 1,
                },
                "entries": [{"fname": "b.md"}],
            },
            {
                "schema_version": 1,
                "batch_id": "02",
                "unresolved_sorted_range": {
                    "start_inclusive": 2,
                    "end_exclusive": 3,
                },
                "entries": [{"fname": "c.md"}],
            },
        ]
        with self.assertRaisesRegex(ValueError, "batch range mismatch"):
            self.adjudicator.validate_batch_metadata(batches, 2)

    def test_adjudicated_artifact_refuses_same_timestamp_overwrite(self):
        output = self.raw_output()
        output["timestamp"] = "2026-07-26T120000000000"
        with tempfile.TemporaryDirectory() as tmp:
            self.adjudicator.write_artifact(output, tmp)
            with self.assertRaises(FileExistsError):
                self.adjudicator.write_artifact(output, tmp)

    def test_default_current_rejects_noncanonical_taxonomy_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            custom = Path(tmp)
            with self.assertRaisesRegex(ValueError, "canonical taxonomy"):
                self.adjudicator.require_canonical_current_target(
                    custom / "taxonomy.json",
                    self.adjudicator.OUTDIR,
                )

            self.adjudicator.require_canonical_current_target(
                custom / "taxonomy.json",
                custom / "output",
            )

        raw = self.raw_output()
        raw["taxonomy_digest"] = "stale"
        with self.assertRaisesRegex(ValueError, "taxonomy digest mismatch"):
            self.adjudicator.adjudicate_output(
                raw,
                {"entries": []},
                [],
                self.taxonomy,
                self.taxonomy_digest,
            )


if __name__ == "__main__":
    unittest.main()
