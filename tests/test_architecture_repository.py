"""Unit tests for the local PIVOT ArchitectureRepository."""

import json
import tempfile
import unittest
from pathlib import Path

from src.architecture_repository import (
    ArchitectureDataUnavailableError,
    ArchitectureRepository,
)


class TestArchitectureRepository(unittest.TestCase):
    """Verify retrieval behavior independently of architecture validation."""

    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_directory.cleanup)

        self.data_directory = Path(self.temp_directory.name)
        self.repository = ArchitectureRepository(self.data_directory)

    def write_json(self, filename, data):
        path = self.data_directory / filename
        path.write_text(json.dumps(data), encoding="utf-8")

    def test_load_valid_components(self):
        """
        Given a valid components JSON file
        When the repository retrieves it
        Then it returns the original component records
        """
        components = [
            {"id": "COMP-001", "name": "BalanceCalculationAPI"}
        ]

        self.write_json("components.json", components)

        result = self.repository.load_components()

        self.assertEqual(result, components)

    def test_load_valid_dependencies(self):
        """
        Given a valid dependencies JSON file
        When the repository retrieves it
        Then it returns the original dependency records
        """
        dependencies = [
            {
                "source": "COMP-001",
                "target": "COMP-002",
            }
        ]

        self.write_json("dependencies.json", dependencies)

        result = self.repository.load_dependencies()

        self.assertEqual(result, dependencies)

    def test_load_valid_business_rules(self):
        """
        Given a valid business rules JSON file
        When the repository retrieves it
        Then it returns the original business rules
        """
        rules = {"rules": []}

        self.write_json("business_rules.json", rules)

        result = self.repository.load_business_rules()

        self.assertEqual(result, rules)

    def test_empty_dependencies_are_accepted(self):
        """
        Given a dependency file containing an empty list
        When the repository retrieves it
        Then it returns the empty list without raising an error
        """
        self.write_json("dependencies.json", [])

        result = self.repository.load_dependencies()

        self.assertEqual(result, [])

    def test_missing_file_raises_explicit_error(self):
        """
        Given a required architecture file is missing
        When the repository attempts retrieval
        Then it raises ArchitectureDataUnavailableError
        """
        with self.assertRaises(ArchitectureDataUnavailableError):
            self.repository.load_dependencies()

    def test_malformed_json_raises_explicit_error(self):
        """
        Given a file containing malformed JSON
        When the repository attempts retrieval
        Then it raises ArchitectureDataUnavailableError
        """
        path = self.data_directory / "dependencies.json"
        path.write_text("{invalid json", encoding="utf-8")

        with self.assertRaises(ArchitectureDataUnavailableError):
            self.repository.load_dependencies()

    def test_invalid_records_are_not_filtered(self):
        """
        Given a structurally questionable dependency record
        When the repository retrieves it
        Then it returns the record for DataValidator to evaluate
        """
        dependencies = [
            {
                "source": "COMP-001",
                "target": "UNKNOWN",
            }
        ]

        self.write_json("dependencies.json", dependencies)

        result = self.repository.load_dependencies()

        self.assertEqual(result, dependencies)

    def test_rejects_directory_traversal(self):
        """
        Given a filename attempting to escape the data directory
        When the repository receives the filename
        Then it rejects the request
        """
        with self.assertRaises(ValueError):
            self.repository.load("../dependencies.json")


if __name__ == "__main__":
    unittest.main()