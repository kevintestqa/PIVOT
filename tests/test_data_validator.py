"""
PIVOT - Data Validator Tests

Purpose:
    Verify the integrity and freshness of architecture dependency records
    before they are used for change-impact analysis.

Testing Approach:
    Gherkin-style acceptance criteria are embedded directly in each
    Python test using Given, When, and Then statements.

Test Coverage:
    PIVOT-005: Duplicate dependency relationships
    PIVOT-006: Completely invalid datasets
    PIVOT-007: Partially invalid datasets
    PIVOT-008: Stale dependency evidence
    PIVOT-009: Verification freshness boundaries
    PIVOT-010: Malformed verification dates
    PIVOT-011: Missing verification evidence
    PIVOT-012: Future verification dates
"""

import unittest
from datetime import date, timedelta

from src.data_validator import DataValidator


class TestDataValidator(unittest.TestCase):
    """Acceptance tests for architecture dependency validation."""

    def setUp(self):
        """Initialize a deterministic test environment."""

        self.assessment_date = date(2026, 10, 17)

        self.components = [
            {"id": "A"},
            {"id": "B"},
            {"id": "C"}
        ]

    def create_dependency(self, record_id, days_old=0):
        """Create a dependency with a predictable verification date."""

        return {
            "id": record_id,
            "source": "A",
            "target": "B",
            "relationship": "PROVIDES_DATA",
            "last_verified": (
                self.assessment_date - timedelta(days=days_old)
            ).isoformat()
        }

    def validate(self, dependencies, threshold=90):
        """Execute validation using a fixed assessment date."""

        validator = DataValidator(
            self.components,
            dependencies,
            threshold_days=threshold
        )

        return validator.validate(self.assessment_date)

    def test_duplicate_dependencies(self):
        """
        PIVOT-005: Detect duplicate dependency relationships.

        Given two records describe the same dependency relationship
        When PIVOT validates the architecture documentation
        Then one duplicate should be identified
        And the duplicate should reference the original record
        """

        dependencies = [
            self.create_dependency("DEP-001"),
            self.create_dependency("DEP-002")
        ]

        result = self.validate(dependencies)

        self.assertEqual(len(result["duplicates"]), 1)

        self.assertEqual(
            result["duplicates"][0]["duplicate_of"],
            "DEP-001"
        )

    def test_all_records_invalid(self):
        """
        PIVOT-006: Identify completely invalid datasets.

        Given all dependency records reference unknown components
        When PIVOT validates the architecture documentation
        Then no dependency records should be considered valid
        And all invalid records should be reported
        """

        dependencies = [
            {"id": "DEP-001", "source": "X", "target": "Y"},
            {"id": "DEP-002", "source": "Z", "target": "Q"}
        ]

        result = self.validate(dependencies)

        self.assertEqual(len(result["valid_records"]), 0)
        self.assertEqual(len(result["invalid_records"]), 2)

    def test_partially_invalid_records(self):
        """
        PIVOT-007: Preserve valid records in partially invalid datasets.

        Given one dependency contains valid component references
        And another dependency references an unknown component
        When PIVOT validates the architecture documentation
        Then the valid dependency should be preserved
        And the invalid dependency should be reported separately
        """

        dependencies = [
            self.create_dependency("DEP-001"),
            {"id": "DEP-002", "source": "A", "target": "X"}
        ]

        result = self.validate(dependencies)

        self.assertEqual(len(result["valid_records"]), 1)
        self.assertEqual(len(result["invalid_records"]), 1)

    def test_stale_dependency(self):
        """
        PIVOT-008: Detect stale dependency evidence.

        Given a dependency was last verified 120 days ago
        And the verification threshold is 90 days
        When PIVOT evaluates the dependency
        Then the dependency should be classified as stale
        """

        dependency = self.create_dependency("DEP-001", 120)

        result = self.validate([dependency])

        self.assertEqual(len(result["stale_records"]), 1)

    def test_freshness_boundaries(self):
        """
        PIVOT-009: Verify the 90-day freshness boundary.

        Given the verification threshold is 90 days
        When PIVOT evaluates dependencies of different ages
        Then dependencies aged 0, 89, and 90 days should remain current
        And dependencies aged 91 and 120 days should be stale

        Scenario Outline:
            Given a dependency was verified <days_old> days ago
            When PIVOT evaluates its verification freshness
            Then the stale result should equal <expected_stale>

        Examples:
            | days_old | expected_stale |
            | 0        | False          |
            | 89       | False          |
            | 90       | False          |
            | 91       | True           |
            | 120      | True           |
        """

        test_cases = [
            (0, False),
            (89, False),
            (90, False),
            (91, True),
            (120, True)
        ]

        for days_old, expected_stale in test_cases:
            with self.subTest(days_old=days_old):

                dependency = self.create_dependency(
                    "DEP-001",
                    days_old
                )

                result = self.validate([dependency])

                self.assertEqual(
                    bool(result["stale_records"]),
                    expected_stale
                )

    def test_configurable_threshold(self):
        """
        PIVOT-009: Verify configurable verification thresholds.

        Given a dependency was verified 120 days ago
        And the verification threshold is configured to 180 days
        When PIVOT evaluates the dependency
        Then the dependency should not be classified as stale
        """

        dependency = self.create_dependency("DEP-001", 120)

        result = self.validate([dependency], threshold=180)

        self.assertEqual(result["stale_records"], [])

    def test_invalid_date(self):
        """
        PIVOT-010: Reject malformed verification dates.

        Given a dependency contains an invalid verification date
        When PIVOT validates the architecture documentation
        Then the dependency should be reported as invalid
        And the dependency should not appear in valid records
        """

        dependency = self.create_dependency("DEP-001")
        dependency["last_verified"] = "invalid-date"

        result = self.validate([dependency])

        self.assertEqual(len(result["invalid_records"]), 1)
        self.assertEqual(len(result["valid_records"]), 0)

    def test_missing_verification_date(self):
        """
        PIVOT-011: Handle missing verification evidence.

        Given a dependency does not contain a last_verified date
        When PIVOT validates the architecture documentation
        Then the dependency should be classified as unverified
        And the dependency should remain available for provisional analysis
        """

        dependency = self.create_dependency("DEP-001")
        dependency.pop("last_verified")

        result = self.validate([dependency])

        self.assertEqual(len(result["unverified_records"]), 1)
        self.assertEqual(len(result["valid_records"]), 1)

    def test_future_verification_date(self):
        """
        PIVOT-012: Reject future verification dates.

        Given a dependency has a verification date in the future
        When PIVOT validates the architecture documentation
        Then the dependency should be reported as invalid
        """

        dependency = self.create_dependency("DEP-001", -1)

        result = self.validate([dependency])

        self.assertEqual(len(result["invalid_records"]), 1)


if __name__ == "__main__":
    unittest.main()