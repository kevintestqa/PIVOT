"""Integration tests for PIVOT AssessmentEngine repository retrieval."""

import json
import tempfile
import unittest
from pathlib import Path

from src.architecture_repository import ArchitectureRepository
from src.assessment_engine import AssessmentEngine

class FakeValidator:
    """Simulate validation without executing real validation rules."""

    def __init__(self, components, dependencies):
        self.components = components
        self.dependencies = dependencies

    def validate(self):
        return {
            "total_records": len(self.dependencies),
            "valid_records": self.dependencies,
            "invalid_records": [],
            "duplicates": [],
            "stale_records": [],
            "unverified_records": [],
        }


class TestAssessmentEngine(unittest.TestCase):
    """Verify assessment states during architecture data retrieval."""

    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_directory.cleanup)

        self.data_directory = Path(self.temp_directory.name)
        self.repository = ArchitectureRepository(self.data_directory)
        self.engine = AssessmentEngine(self.repository)

    def write_json(self, filename, data):
        """Write a synthetic dataset to the temporary repository."""
        (self.data_directory / filename).write_text(
            json.dumps(data),
            encoding="utf-8",
        )

    def test_successful_retrieval(self):
        """
        Given all required architecture datasets exist
        When AssessmentEngine retrieves the data
        Then it reports READY_FOR_VALIDATION without calculating risk
        """
        self.write_json("components.json", [{"id": "COMP-001"}])
        self.write_json("dependencies.json", [])
        self.write_json("business_rules.json", [])

        result = self.engine.assess("CR-001", "COMP-001")

        self.assertEqual(result["assessment_state"], "READY_FOR_VALIDATION")
        self.assertIsNone(result["risk_level"])
        self.assertIsNone(result["weighted_score"])
        self.assertEqual(
            result["retrieved_record_counts"],
            {"components": 1, "dependencies": 0, "business_rules": 0},
        )

    def test_missing_dependency_file(self):
        """
        Given the dependency dataset is missing
        When AssessmentEngine attempts retrieval
        Then it returns UNAVAILABLE with no risk score
        """
        self.write_json("components.json", [{"id": "COMP-001"}])
        self.write_json("business_rules.json", [])

        result = self.engine.assess("CR-001", "COMP-001")

        self.assertEqual(result["assessment_state"], "UNAVAILABLE")
        self.assertIsNone(result["risk_level"])
        self.assertIsNone(result["weighted_score"])
        self.assertIn("dependencies.json", result["reason"])

    def test_malformed_business_rules(self):
        """
        Given the business-rule dataset contains malformed JSON
        When AssessmentEngine attempts retrieval
        Then it returns UNAVAILABLE instead of raising an exception
        """
        self.write_json("components.json", [{"id": "COMP-001"}])
        self.write_json("dependencies.json", [])

        (self.data_directory / "business_rules.json").write_text(
            "{invalid json",
            encoding="utf-8",
        )

        result = self.engine.assess("CR-001", "COMP-001")

        self.assertEqual(result["assessment_state"], "UNAVAILABLE")
        self.assertIn("business_rules.json", result["reason"])

    def test_empty_dependencies_are_retrieved(self):
        """
        Given an existing dependency dataset is empty
        When AssessmentEngine retrieves the data
        Then retrieval succeeds without assuming the architecture is complete
        """
        self.write_json("components.json", [{"id": "COMP-001"}])
        self.write_json("dependencies.json", [])
        self.write_json("business_rules.json", [])

        result = self.engine.assess("CR-001", "COMP-001")

        self.assertEqual(result["assessment_state"], "READY_FOR_VALIDATION")
        self.assertEqual(
            result["retrieved_record_counts"]["dependencies"], 0
        )
    
    
    def test_successful_retrieval_runs_injected_validator(self):
        """An injected validator should run after successful retrieval."""
        components = [{"id": "COMP-001"}]
        dependencies = []

        self.write_json("components.json", components)
        self.write_json("dependencies.json", dependencies)
        self.write_json("business_rules.json", [])

        engine = AssessmentEngine(self.repository, validator=FakeValidator)
        result = engine.assess("CR-001", "COMP-001")

        self.assertEqual(result["validation_results"]["total_records"], 0)
        self.assertEqual(result["validation_results"]["valid_records"], [])


if __name__ == "__main__":
    unittest.main()