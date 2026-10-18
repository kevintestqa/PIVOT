"""
PIVOT - Deterministic Risk Engine

Purpose:
    Calculate the potential business risk of a proposed application change.

Responsibilities:
    - Evaluate aggregate criticality of impacted components.
    - Evaluate the scope of potential downstream impacts.
    - Incorporate documented business-rule sensitivity.
    - Support organization-specific scoring configurations.
    - Apply deterministic critical-business-control safeguards.
    - Return explainable risk assessments.

Scoring Model:
    Component Criticality:    40%
    Impact Scope:             30%
    Business Rule Sensitivity: 30%

Risk Classification:
    LOW:     Score < 40
    MEDIUM:  40 <= Score < 75
    HIGH:    Score >= 75

Architectural Principles:
    - Risk scoring is deterministic.
    - Components are counted only once.
    - AI cannot override calculated risk.
    - Evidence confidence is separate from business risk.
    - PIVOT does not automatically approve or reject releases.

Limitations:
    Initial weights and thresholds are design assumptions.
    They have not been calibrated against historical incidents.
"""

DEFAULT_CONFIG = {
    "weights": {
        "component_criticality": 0.40,
        "impact_scope": 0.30,
        "business_rule_sensitivity": 0.30
    },
    "thresholds": {
        "low": 40,
        "high": 75
    },
    "scope_cap": 5
}

CRITICALITY_VALUES = {
    "LOW": 1,
    "MEDIUM": 2,
    "HIGH": 3
}

SENSITIVITY_VALUES = {
    "LOW": 0,
    "MEDIUM": 50,
    "HIGH": 100
}


class RiskEngine:
    """Calculate explainable business risk using configurable weights."""

    def __init__(self, config=None):
        """Initialize and validate the organization's scoring configuration."""

        self.config = config if config is not None else DEFAULT_CONFIG

        self.weights = self.config["weights"]
        self.thresholds = self.config["thresholds"]
        self.scope_cap = self.config.get("scope_cap", 5)

        required_factors = {
            "component_criticality",
            "impact_scope",
            "business_rule_sensitivity"
        }

        if set(self.weights) != required_factors:
            raise ValueError("Exactly three scoring weights are required")

        if any(
            not isinstance(value, (int, float))
            or isinstance(value, bool)
            or not 0 <= value <= 1
            for value in self.weights.values()
        ):
            raise ValueError("Each weight must be between 0 and 1")

        if abs(sum(self.weights.values()) - 1.0) > 1e-9:
            raise ValueError("Scoring weights must total 1.0")

        if not (
            0 <= self.thresholds["low"]
            < self.thresholds["high"]
            <= 100
        ):
            raise ValueError("Invalid risk thresholds")

        if (
            not isinstance(self.scope_cap, int)
            or isinstance(self.scope_cap, bool)
            or self.scope_cap < 1
        ):
            raise ValueError("scope_cap must be a positive integer")

    def assess(
        self,
        change_id,
        impacts,
        components,
        business_rule_sensitivity,
        critical_business_control=False
    ):
        """
        Calculate risk for a proposed change.

        Args:
            change_id:
                Unique identifier for the proposed change.

            impacts:
                List of impacted components returned by DependencyAnalyzer.

            components:
                Architecture component records containing criticality.

            business_rule_sensitivity:
                Documented sensitivity: LOW, MEDIUM, or HIGH.

            critical_business_control:
                Whether documented evidence identifies a critical
                business control affected by the proposed change.

        Returns:
            Dictionary containing risk classification, weighted score,
            factor breakdown, safeguards, and explanatory reasons.

        Raises:
            ValueError:
                If supplied component or business-rule data is invalid.
        """

        if business_rule_sensitivity not in SENSITIVITY_VALUES:
            raise ValueError("Unknown business rule sensitivity")

        if not isinstance(critical_business_control, bool):
            raise ValueError(
                "critical_business_control must be boolean"
            )

        component_map = {
            component["id"]: component
            for component in components
        }

        # Count each impacted component once, regardless of path count.
        impacted_ids = sorted({
            impact["component_id"]
            for impact in impacts
        })

        criticality_values = []

        for component_id in impacted_ids:

            if component_id not in component_map:
                raise ValueError(
                    f"Unknown impacted component: {component_id}"
                )

            criticality = component_map[component_id]["criticality"]

            if criticality not in CRITICALITY_VALUES:
                raise ValueError(
                    f"Invalid criticality for {component_id}"
                )

            criticality_values.append(
                CRITICALITY_VALUES[criticality]
            )

        # Normalize aggregate criticality to a 0–100 scale.
        if criticality_values:
            average_criticality = (
                sum(criticality_values) / len(criticality_values)
            )

            criticality_score = (
                (average_criticality - 1) / 2
            ) * 100
        else:
            criticality_score = 0

        # Normalize the number of unique impacted components.
        scope_score = min(
            len(impacted_ids) / self.scope_cap,
            1
        ) * 100

        sensitivity_score = SENSITIVITY_VALUES[
            business_rule_sensitivity
        ]

        factor_scores = {
            "component_criticality": round(criticality_score, 2),
            "impact_scope": round(scope_score, 2),
            "business_rule_sensitivity": sensitivity_score
        }

        weighted_score = round(
            sum(
                factor_scores[factor] * self.weights[factor]
                for factor in factor_scores
            ),
            2
        )

        # Apply configured risk thresholds.
        if weighted_score >= self.thresholds["high"]:
            weighted_level = "HIGH"

        elif weighted_score >= self.thresholds["low"]:
            weighted_level = "MEDIUM"

        else:
            weighted_level = "LOW"

        # A documented critical business control establishes a floor.
        guardrail_applied = (
            critical_business_control
            and weighted_level != "HIGH"
        )

        final_level = (
            "HIGH"
            if critical_business_control
            else weighted_level
        )

        reasons = [
            f"{len(impacted_ids)} unique downstream components assessed",
            f"Business rule sensitivity: {business_rule_sensitivity}"
        ]

        if critical_business_control:
            reasons.append(
                "Documented critical business control: minimum HIGH risk"
            )

        return {
            "change_id": change_id,
            "weighted_score": weighted_score,
            "weighted_level": weighted_level,
            "risk_level": final_level,
            "guardrail_applied": guardrail_applied,
            "impacted_component_count": len(impacted_ids),
            "factor_scores": factor_scores,
            "weights": dict(self.weights),
            "reasons": reasons
        }