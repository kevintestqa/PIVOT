"""
PIVOT - Dependency Analyzer Tests

Purpose:
    Validate the deterministic dependency analysis engine.

Testing Approach:
    Each test includes Gherkin-style acceptance criteria using
    Given, When, and Then statements.

    Tests verify documented potential impacts, not confirmed failures.

Test Coverage:
    PIVOT-001: Direct and indirect dependencies
    PIVOT-002: Isolated components
    PIVOT-003: Circular dependencies
    PIVOT-004: Invalid dependency references
"""

import json
import unittest
from pathlib import Path

from src.analyzer import DependencyAnalyzer


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class TestDependencyAnalyzer(unittest.TestCase):
    """Automated acceptance tests for dependency impact analysis."""

    def setUp(self):
        """
        Given the Apex Trading architecture documentation
        When the test environment is initialized
        Then the dependency analyzer is loaded with documented components
        And their dependency relationships
        """

        with open(PROJECT_ROOT / "data/components.json") as file:
            components = json.load(file)["components"]

        with open(PROJECT_ROOT / "data/dependencies.json") as file:
            dependencies = json.load(file)["dependencies"]

        self.analyzer = DependencyAnalyzer(components, dependencies)

    def test_direct_and_indirect_impacts(self):
        """
        PIVOT-001: Verify direct and indirect impact paths.

        Given COMP-001 has documented dependencies on downstream components
        And COMP-002 can be reached through multiple dependency paths
        When PIVOT analyzes a proposed change to COMP-001
        Then COMP-002, COMP-003, and COMP-004 should be identified
        And COMP-002 should be classified as DIRECT and INDIRECT
        And all documented impact paths should be preserved
        """

        results = self.analyzer.find_impacted_components("COMP-001")

        impacts = {
            result["component_id"]: result
            for result in results
        }

        self.assertEqual(
            set(impacts.keys()),
            {"COMP-002", "COMP-003", "COMP-004"}
        )

        self.assertEqual(
            set(impacts["COMP-002"]["impact_types"]),
            {"DIRECT", "INDIRECT"}
        )

        self.assertCountEqual(
            impacts["COMP-002"]["paths"],
            [
                ["COMP-001", "COMP-002"],
                ["COMP-001", "COMP-003", "COMP-002"]
            ]
        )

    def test_isolated_component(self):
        """
        PIVOT-002: Verify a component without downstream dependencies.

        Given COMP-007 has no documented downstream dependencies
        When PIVOT analyzes a proposed change to COMP-007
        Then no downstream components should be identified
        And the analyzer should return an empty result
        """

        results = self.analyzer.find_impacted_components("COMP-007")

        self.assertEqual(results, [])

    def test_circular_dependencies(self):
        """
        PIVOT-003: Verify circular dependencies do not cause infinite loops.

        Given component A has a dependency relationship with B
        And component B has a dependency relationship with C
        And component C has a dependency relationship with A
        When PIVOT analyzes a proposed change to component A
        Then component B should be identified as DIRECT
        And component C should be identified as INDIRECT
        And component A should not be reported as its own downstream impact
        And dependency traversal should terminate successfully
        """

        components = [
            {"id": "A"},
            {"id": "B"},
            {"id": "C"}
        ]

        dependencies = [
            {"source": "A", "target": "B"},
            {"source": "B", "target": "C"},
            {"source": "C", "target": "A"}
        ]

        analyzer = DependencyAnalyzer(components, dependencies)

        results = analyzer.find_impacted_components("A")

        impacts = {
            result["component_id"]: result
            for result in results
        }

        self.assertEqual(set(impacts.keys()), {"B", "C"})

        self.assertEqual(
            impacts["B"]["impact_types"],
            ["DIRECT"]
        )

        self.assertEqual(
            impacts["C"]["impact_types"],
            ["INDIRECT"]
        )

    def test_invalid_dependency_reference(self):
        """
        PIVOT-004: Verify invalid component references are rejected.

        Given the architecture contains components A and B
        And a dependency references an unknown component X
        When PIVOT attempts to construct the dependency graph
        Then the analyzer should raise a ValueError
        And the error should identify the unknown component X
        """

        components = [
            {"id": "A"},
            {"id": "B"}
        ]

        dependencies = [
            {"source": "A", "target": "X"}
        ]

        with self.assertRaisesRegex(
            ValueError,
            "Unknown target component: X"
        ):
            DependencyAnalyzer(components, dependencies)


if __name__ == "__main__":
    unittest.main()