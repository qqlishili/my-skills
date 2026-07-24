import json
import re
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TAXONOMY_PATH = PROJECT_ROOT / "references" / "taxonomy.json"
MODELS_DIR = PROJECT_ROOT / "references" / "models"
CATALOG_PATH = PROJECT_ROOT / "references" / "heuristics" / "catalog.md"


def load_taxonomy():
    if not TAXONOMY_PATH.exists():
        raise AssertionError(f"missing taxonomy: {TAXONOMY_PATH}")
    return json.loads(TAXONOMY_PATH.read_text(encoding="utf-8"))


def frontmatter_value(path, key):
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not match:
        raise AssertionError(f"missing frontmatter: {path}")
    for line in match.group(1).splitlines():
        name, separator, value = line.partition(":")
        if separator and name.strip() == key:
            return value.strip().strip("\"'")
    raise AssertionError(f"missing {key} in frontmatter: {path}")


def catalog_ids():
    if not CATALOG_PATH.exists():
        raise AssertionError(f"missing heuristic catalog: {CATALOG_PATH}")
    text = CATALOG_PATH.read_text(encoding="utf-8")
    return set(re.findall(r"^##\s+(h\d{2})\b", text, re.MULTILINE))


def normalized_text(value):
    return re.sub(r"\s+", "", value).translate(str.maketrans("，。", ",."))


class TaxonomyConsistencyTests(unittest.TestCase):
    def test_taxonomy_uses_g2_approved_counts_and_unique_ids(self):
        taxonomy = load_taxonomy()
        model_ids = [model["id"] for model in taxonomy["models"]]
        heuristic_ids = [
            heuristic["id"] for heuristic in taxonomy["heuristics"]
        ]

        self.assertEqual(taxonomy["schema_version"], 1)
        self.assertEqual(len(model_ids), 6)
        self.assertEqual(len(set(model_ids)), 6)
        self.assertEqual(model_ids, [f"m{i:02d}" for i in range(1, 7)])
        self.assertEqual(len(heuristic_ids), 9)
        self.assertEqual(len(set(heuristic_ids)), 9)
        self.assertEqual(heuristic_ids, [f"h{i:02d}" for i in range(1, 10)])

    def test_model_documents_match_taxonomy(self):
        taxonomy = load_taxonomy()
        taxonomy_ids = {model["id"] for model in taxonomy["models"]}
        model_docs = list(MODELS_DIR.glob("m??-*.md"))
        document_ids = {
            frontmatter_value(path, "taxonomy_id") for path in model_docs
        }

        self.assertEqual(len(model_docs), 6)
        self.assertEqual(document_ids, taxonomy_ids)

    def test_heuristic_catalog_matches_taxonomy(self):
        taxonomy = load_taxonomy()
        taxonomy_ids = {
            heuristic["id"] for heuristic in taxonomy["heuristics"]
        }
        self.assertEqual(catalog_ids(), taxonomy_ids)

    def test_legacy_heuristics_have_complete_dispositions(self):
        taxonomy = load_taxonomy()
        mappings = taxonomy["legacy_heuristic_mapping"]
        legacy_ids = [mapping["legacy_id"] for mapping in mappings]
        current_ids = {
            heuristic["id"] for heuristic in taxonomy["heuristics"]
        }
        valid_dispositions = {"retained", "merged", "split", "retired"}

        self.assertEqual(legacy_ids, [f"h{i:02d}" for i in range(1, 18)])
        self.assertTrue(
            all(
                mapping["disposition"] in valid_dispositions
                and mapping["reason"].strip()
                for mapping in mappings
            )
        )
        for mapping in mappings:
            self.assertTrue(
                set(mapping["current_ids"]) <= current_ids,
                f"{mapping['legacy_id']} maps to an unknown heuristic",
            )

    def test_evidence_paths_lines_and_quotes_are_traceable(self):
        taxonomy = load_taxonomy()
        evidence_records = []
        for model in taxonomy["models"]:
            evidence_records.extend(model["supporting_evidence"])
            evidence_records.append(model["counterexample"])
        for heuristic in taxonomy["heuristics"]:
            evidence_records.extend(heuristic["supporting_evidence"])

        for evidence in evidence_records:
            path = PROJECT_ROOT / evidence["path"]
            self.assertTrue(path.is_file(), f"missing evidence path: {path}")
            lines = path.read_text(encoding="utf-8").splitlines()
            line_number = evidence["line"]
            self.assertGreaterEqual(line_number, 1)
            self.assertLessEqual(line_number, len(lines))
            self.assertIn(
                normalized_text(evidence["quote"]),
                normalized_text(lines[line_number - 1]),
                f"evidence quote not found at {path}:{line_number}",
            )

    def test_legacy_assets_are_preserved(self):
        taxonomy = load_taxonomy()
        legacy_paths = (
            taxonomy["legacy_assets"]["models"]
            + taxonomy["legacy_assets"]["heuristics"]
        )
        self.assertEqual(len(legacy_paths), 7)
        for relative_path in legacy_paths:
            self.assertTrue(
                (PROJECT_ROOT / relative_path).is_file(),
                f"missing legacy asset: {relative_path}",
            )

    def test_models_are_descriptive_and_heuristics_reference_models(self):
        taxonomy = load_taxonomy()
        model_ids = {model["id"] for model in taxonomy["models"]}

        for model in taxonomy["models"]:
            for key in (
                "definition",
                "routing_terms",
                "inputs",
                "state_variables",
                "outputs",
                "applicable_questions",
                "failure_boundary",
                "supporting_evidence",
                "counterexample",
            ):
                self.assertTrue(model[key], f"{model['id']} missing {key}")

        for heuristic in taxonomy["heuristics"]:
            self.assertIn(heuristic["status"], {"confirmed", "provisional"})
            self.assertGreaterEqual(len(heuristic["routing_terms"]), 4)
            self.assertEqual(
                len(heuristic["routing_terms"]),
                len(set(heuristic["routing_terms"])),
            )
            self.assertGreaterEqual(len(heuristic["supporting_evidence"]), 2)
            self.assertTrue(heuristic["failure_boundary"])
            self.assertTrue(heuristic["applicable_scenarios"])
            self.assertTrue(heuristic["disabled_conditions"])
            self.assertTrue(set(heuristic["related_model_ids"]) <= model_ids)

        for model in taxonomy["models"]:
            self.assertGreaterEqual(len(model["routing_terms"]), 4)
            self.assertEqual(
                len(model["routing_terms"]),
                len(set(model["routing_terms"])),
            )


if __name__ == "__main__":
    unittest.main()
