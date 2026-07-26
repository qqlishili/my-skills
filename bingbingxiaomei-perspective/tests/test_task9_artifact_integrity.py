import hashlib
import json
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTDIR = PROJECT_ROOT / "scripts" / "classification_output"
EVALS = PROJECT_ROOT / "evals"
RAW_ARTIFACT = OUTDIR / "classification-2026-07-26T142953.json"
POINTER = OUTDIR / "current.json"
QUEUE = EVALS / "current-classification-review-2026-07-26.json"
STATUS = EVALS / "current-classification-review-status-2026-07-26.json"


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


class Task9ArtifactIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = load_json(RAW_ARTIFACT)
        cls.pointer = load_json(POINTER)
        cls.current_path = OUTDIR / cls.pointer["path"]
        cls.current = load_json(cls.current_path)
        cls.queue = load_json(QUEUE)
        cls.status = load_json(STATUS)
        cls.manual = load_json(
            EVALS / "current-classification-manual-review-2026-07-26.json"
        )
        cls.batches = [
            load_json(path)
            for path in sorted(
                (EVALS / "review-batches").glob(
                    "task9-unresolved-batch-*.json"
                )
            )
        ]

    def test_current_pointer_and_provenance_match_raw_artifact(self):
        self.assertEqual(
            hashlib.sha256(self.current_path.read_bytes()).hexdigest(),
            self.pointer["sha256"],
        )
        self.assertEqual(self.current["classification_stage"], "adjudicated")
        self.assertEqual(self.current["total_articles"], 520)
        self.assertEqual(self.current["unresolved_count"], 228)
        raw_by_name = {item["fname"]: item for item in self.raw["per_article"]}
        for item in self.current["per_article"]:
            raw = raw_by_name[item["fname"]]
            self.assertEqual(
                item["classifier_primary_model_id"],
                raw["primary_model_id"],
            )
            self.assertEqual(item["classifier_unresolved"], raw["unresolved"])
            self.assertEqual(
                item["classifier_confidence"],
                float(raw["confidence"]),
            )

    def test_batches_exactly_cover_raw_unresolved_set(self):
        entries = [entry for batch in self.batches for entry in batch["entries"]]
        expected = {
            item["fname"]
            for item in self.raw["per_article"]
            if item["unresolved"]
        }
        actual = {entry["fname"] for entry in entries}
        self.assertEqual(len(self.batches), 6)
        self.assertEqual(len(entries), len(actual))
        self.assertEqual(actual, expected)

    def test_queue_and_status_both_report_complete_review(self):
        self.assertEqual(self.queue["review_status_counts"], {"reviewed": 358})
        self.assertTrue(
            all(item["review_status"] == "reviewed" for item in self.queue["items"])
        )
        self.assertEqual(self.status["reviewed_total"], 358)
        self.assertEqual(self.status["pending_total"], 0)
        self.assertEqual(
            self.status["gate_status"],
            "passed_task9_data_prerequisite",
        )
        self.assertEqual(
            Path(self.status["adjudicated_artifact"]).name,
            self.pointer["path"],
        )


if __name__ == "__main__":
    unittest.main()
