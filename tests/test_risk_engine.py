"""
PIVOT Risk Engine Unit Tests

Purpose:
    Validate deterministic business-risk scoring.

Test Coverage:
    - LOW, MEDIUM, and HIGH classifications
    - Risk threshold boundaries
    - Aggregate component criticality
    - Duplicate impacted components
    - Organization-specific scoring configurations
    - Invalid configuration weights
    - Critical business control safeguards
    - Invalid component references
    - Invalid business-rule sensitivity
    - No documented downstream impacts

Testing Framework:
    Python unittest

Test Design:
    Given/When/Then descriptions are embedded in test docstrings.
"""

import unittest

from src.risk_engine import RiskEngine


class TestRiskEngine(unittest.TestCase):
    """Verify PIVOT's deterministic risk-scoring behavior."""

    def setUp(self):
        """Create reusable test components and the default RiskEngine."""

        self.engine = RiskEngine()

        self.components = [
            {"id": "LOW-1", "criticality": "LOW"},
            {"id": "LOW-2", "criticality": "LOW"},
            {"id": "MED-1", "criticality": "MEDIUM"},
            {"id": "HIGH-1", "criticality": "HIGH"},
            {"id": "HIGH-2", "criticality": "HIGH"},
        ]

    def assess(
        self,
        component_ids,
        sensitivity="LOW",
        critical_control=False,
        engine=None,
    ):
        """Build a test assessment using documented component identifiers."""

        selected_engine = engine if engine is not None else self.engine

        return selected_engine.assess(
            change_id="CR-TEST",
            impacts=[
                {"component_id": component_id}
                for component_id in component_ids
            ],
            components=self.components,
            business_rule_sensitivity=sensitivity,
            critical_business_control=critical_control,
        )

    def test_pivot_013_low_risk(self):
        """
        Given one LOW-criticality component and LOW business sensitivity
        When the RiskEngine evaluates the proposed change
        Then the risk classification should be LOW.
        """

        result = self.assess(["LOW-1"])

        self.assertEqual(result["risk_level"], "LOW")
        self.assertEqual(result["weighted_score"], 6.0)

        self.assertEqual(
            result["factor_scores"]["component_criticality"],
            0,
        )

        self.assertEqual(
            result["factor_scores"]["impact_scope"],
            20,
        )

    def test_pivot_014_medium_risk(self):
        """
        Given one MEDIUM-criticality component
        And MEDIUM business-rule sensitivity
        When the RiskEngine evaluates the proposed change
        Then the risk classification should be MEDIUM.
        """

        result = self.assess(
            ["MED-1"],
            sensitivity="MEDIUM",
        )

        self.assertEqual(result["weighted_score"], 41.0)
        self.assertEqual(result["risk_level"], "MEDIUM")

    def test_pivot_015_high_risk(self):
        """
        Given two HIGH-criticality components
        And HIGH business-rule sensitivity
        When the RiskEngine evaluates the proposed change
        Then the risk classification should be HIGH.
        """

        result = self.assess(
            ["HIGH-1", "HIGH-2"],
            sensitivity="HIGH",
        )

        self.assertEqual(result["weighted_score"], 82.0)
        self.assertEqual(result["risk_level"], "HIGH")

    def test_pivot_016_threshold_boundaries(self):
        """
        Given organization-specific risk thresholds
        And a deterministic weighted score of 50
        When the score falls immediately below or exactly on a threshold
        Then the correct risk classification should be returned.
        """

        test_cases = [
            ({"low": 50, "high": 75}, "MEDIUM"),
            ({"low": 50.01, "high": 75}, "LOW"),
            ({"low": 40, "high": 50}, "HIGH"),
            ({"low": 40, "high": 50.01}, "MEDIUM"),
        ]

        for thresholds, expected_level in test_cases:

            with self.subTest(thresholds=thresholds):

                config = {
                    "weights": {
                        "component_criticality": 0,
                        "impact_scope": 0,
                        "business_rule_sensitivity": 1,
                    },
                    "thresholds": thresholds,
                }

                custom_engine = RiskEngine(config)

                result = self.assess(
                    [],
                    sensitivity="MEDIUM",
                    engine=custom_engine,
                )

                self.assertEqual(result["weighted_score"], 50)

                self.assertEqual(
                    result["risk_level"],
                    expected_level,
                )

    def test_pivot_017_aggregate_criticality(self):
        """
        Given one HIGH-criticality component
        And one LOW-criticality component
        When the RiskEngine calculates aggregate criticality
        Then both components should reflect the maximum downstream criticality.
        """

        result = self.assess(["HIGH-1", "LOW-1"])

        self.assertEqual(
            result["factor_scores"]["component_criticality"],
            100,
        )

        self.assertEqual(
            result["impacted_component_count"],
            2,
        )

    def test_pivot_018_duplicate_impacts(self):
        """
        Given a component reached through multiple dependency paths
        When the RiskEngine calculates impact scope
        Then that component should only be counted once.
        """

        unique_result = self.assess(
            ["HIGH-1", "LOW-1"]
        )

        duplicate_result = self.assess(
            ["HIGH-1", "LOW-1", "HIGH-1", "HIGH-1"]
        )

        self.assertEqual(
            unique_result["weighted_score"],
            duplicate_result["weighted_score"],
        )

        self.assertEqual(
            duplicate_result["impacted_component_count"],
            2,
        )

    def test_pivot_019_organization_weights(self):
        """
        Given an organization-specific scoring configuration
        When the same proposed change is evaluated
        Then the weighted score should reflect that configuration.
        """

        custom_config = {
            "weights": {
                "component_criticality": 0.20,
                "impact_scope": 0.20,
                "business_rule_sensitivity": 0.60,
            },
            "thresholds": {
                "low": 40,
                "high": 75,
            },
            "scope_cap": 5,
        }

        custom_engine = RiskEngine(custom_config)

        default_result = self.assess(
            ["HIGH-1"],
            sensitivity="LOW",
        )

        custom_result = self.assess(
            ["HIGH-1"],
            sensitivity="LOW",
            engine=custom_engine,
        )

        self.assertEqual(
            default_result["weighted_score"],
            46,
        )

        self.assertEqual(
            custom_result["weighted_score"],
            24,
        )

    def test_pivot_020_invalid_weights(self):
        """
        Given scoring weights that exceed 100 percent
        When the RiskEngine is initialized
        Then the configuration should be rejected.
        """

        invalid_config = {
            "weights": {
                "component_criticality": 0.40,
                "impact_scope": 0.40,
                "business_rule_sensitivity": 0.40,
            },
            "thresholds": {
                "low": 40,
                "high": 75,
            },
        }

        with self.assertRaisesRegex(
            ValueError,
            "total 1.0",
        ):
            RiskEngine(invalid_config)

    def test_pivot_021_critical_control_guardrail(self):
        """
        Given a LOW weighted risk score
        And documented evidence of a critical business control
        When the RiskEngine evaluates the proposed change
        Then the final risk classification should be HIGH
        And the original weighted score should remain visible.
        """

        result = self.assess(
            ["LOW-1"],
            critical_control=True,
        )

        self.assertEqual(result["weighted_level"], "LOW")
        self.assertEqual(result["risk_level"], "HIGH")

        self.assertTrue(result["guardrail_applied"])

        self.assertEqual(
            result["weighted_score"],
            6,
        )

    def test_pivot_022_unknown_component(self):
        """
        Given an impacted component missing from architecture records
        When the RiskEngine evaluates the proposed change
        Then the assessment should be rejected.
        """

        with self.assertRaisesRegex(
            ValueError,
            "Unknown impacted component",
        ):
            self.assess(["MISSING"])

    def test_pivot_023_invalid_sensitivity(self):
        """
        Given an unsupported business-rule sensitivity
        When the RiskEngine evaluates the proposed change
        Then the assessment should be rejected.
        """

        with self.assertRaisesRegex(
            ValueError,
            "Unknown business rule sensitivity",
        ):
            self.assess(
                ["LOW-1"],
                sensitivity="CRITICAL",
            )

    def test_pivot_024_no_documented_impacts(self):
        """
        Given no documented downstream impacts
        And LOW business-rule sensitivity
        When the RiskEngine evaluates the proposed change
        Then the impact-based score should be zero
        And no downstream components should be invented.
        """

        result = self.assess([])

        self.assertEqual(result["weighted_score"], 0)
        self.assertEqual(result["impacted_component_count"], 0)
        self.assertEqual(result["risk_level"], "LOW")

    def test_pivot_025_source_without_downstream(self):
        """
        Given a HIGH-criticality source component
        And no documented downstream dependencies
        When the RiskEngine evaluates the change
        Then source criticality should contribute 100%
        And downstream impact scope should remain zero.
        """

        result = self.engine.assess(
            change_id="CR-025",
            source_component_id="HIGH-1",
            impacts=[],
            components=self.components,
            business_rule_sensitivity="LOW",
        )

        self.assertEqual(result["source_criticality_score"], 100)
        self.assertEqual(result["downstream_criticality_score"], 0)
        self.assertEqual(
            result["factor_scores"]["component_criticality"], 100
        )
        self.assertEqual(result["impacted_component_count"], 0)
        self.assertEqual(result["weighted_score"], 40)
        self.assertEqual(result["risk_level"], "MEDIUM")

    def test_pivot_026_source_downstream_weighting(self):
        """
        Given a HIGH-criticality source component
        And two LOW-criticality downstream components
        When the RiskEngine evaluates the change
        Then source criticality should contribute 60%
        And downstream criticality should contribute 40%.
        """

        result = self.engine.assess(
            change_id="CR-026",
            source_component_id="HIGH-1",
            impacts=[
                {"component_id": "LOW-1"},
                {"component_id": "LOW-2"},
            ],
            components=self.components,
            business_rule_sensitivity="LOW",
        )

        self.assertEqual(result["source_criticality_score"], 100)
        self.assertEqual(result["downstream_criticality_score"], 0)
        self.assertEqual(
            result["factor_scores"]["component_criticality"], 100
        )
        self.assertEqual(result["weighted_score"], 52)
        self.assertEqual(result["risk_level"], "MEDIUM")

    def test_pivot_027_duplicate_downstream_components(self):
        """
        Given a HIGH-criticality source component
        And duplicate references to a LOW-criticality downstream component
        When the RiskEngine evaluates the change
        Then the downstream component should only be counted once.
        """

        result = self.engine.assess(
            change_id="CR-027",
            source_component_id="HIGH-1",
            impacts=[
                {"component_id": "LOW-1"},
                {"component_id": "LOW-1"},
                {"component_id": "LOW-1"},
            ],
            components=self.components,
            business_rule_sensitivity="LOW",
        )

        self.assertEqual(result["impacted_component_count"], 1)
        self.assertEqual(
            result["factor_scores"]["impact_scope"], 20
        )
        self.assertEqual(result["weighted_score"], 46)

    def test_pivot_028_unknown_source_component(self):
        """
        Given a source component missing from architecture records
        When the RiskEngine evaluates the proposed change
        Then the assessment should be rejected
        Rather than assuming a criticality value.
        """

        with self.assertRaisesRegex(
            ValueError,
            "Unknown source component",
        ):
            self.engine.assess(
                change_id="CR-028",
                source_component_id="UNKNOWN-SOURCE",
                impacts=[],
                components=self.components,
                business_rule_sensitivity="LOW",
            )
            
    def test_pivot_029_adding_exposure_cannot_lower_risk(self):
        """
        Given a LOW-criticality source and a HIGH-criticality dependency
        When an additional LOW-criticality dependency is discovered
        Then calculated risk must not decrease.
        """

        common = {
            "source_component_id": "LOW-1",
            "components": self.components,
            "business_rule_sensitivity": "LOW",
        }

        before = self.engine.assess(
            change_id="CR-029-A",
            impacts=[
                {"component_id": "HIGH-1"},
            ],
            **common,
        )

        after = self.engine.assess(
            change_id="CR-029-B",
            impacts=[
                {"component_id": "HIGH-1"},
                {"component_id": "LOW-2"},
            ],
            **common,
        )

        self.assertEqual(
            before["factor_scores"]["component_criticality"],
            40,
        )

        self.assertEqual(
            after["factor_scores"]["component_criticality"],
            40,
        )

        self.assertEqual(before["weighted_score"], 22)
        self.assertEqual(after["weighted_score"], 28)

        self.assertGreaterEqual(
            after["weighted_score"],
            before["weighted_score"],
        )
            
if __name__ == "__main__":
    unittest.main()