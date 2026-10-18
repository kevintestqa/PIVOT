import json
import unittest
from pathlib import Path

from src.analyzer import DependencyAnalyzer


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class TestDependencyAnalyzer(unittest.TestCase):

    def setUp(self):
        """
        Load the Apex Trading test data before each test.
        """
        with open(PROJECT_ROOT / "data/components.json") as file:
            components = json.load(file)["components"]

        with open(PROJECT_ROOT / "data/dependencies.json") as file:
            dependencies = json.load(file)["dependencies"]

        self.analyzer = DependencyAnalyzer(components, dependencies)

    def test_direct_and_indirect_impacts(self):
        """
        PIVOT-001: Verify direct and indirect impact paths.
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
        """
        results = self.analyzer.find_impacted_components("COMP-007")

        self.assertEqual(results, [])

    def test_circular_dependencies(self):
        """
        PIVOT-003: Verify circular dependencies don't cause infinite loops.
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