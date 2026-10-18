"""
PIVOT - Deterministic Risk Engine

Purpose:
    Calculate the potential business risk of a proposed application change.

Responsibilities:
    - Evaluate source component criticality.
    - Evaluate aggregate downstream component criticality.
    - Evaluate the scope of potential downstream impacts.
    - Incorporate documented business-rule sensitivity.
    - Support organization-specific scoring configurations.
    - Apply deterministic critical-business-control safeguards.
    - Return explainable risk assessments.

Scoring Model:
    Component Criticality:     40%
    Impact Scope:              30%
    Business Rule Sensitivity: 30%

Component Criticality:
    With downstream impacts:
        60% source + 40% aggregate downstream

    Without documented downstream impacts:
        100% source

Risk Classification:
    LOW:     Score < 40
    MEDIUM:  40 <= Score < 75
    HIGH:    Score >= 75

Architectural Principles:
    - Risk scoring is deterministic.
    - Downstream components are counted only once.
    - AI cannot override calculated risk.
    - Evidence confidence is separate from business risk.
    - PIVOT does not automatically approve or reject releases.
    - No documented dependencies does not prove no dependencies exist.

Limitations:
    Initial weights and thresholds are design assumptions.
    They have not been calibrated against historical incidents.
"""

DEFAULT_CONFIG = {
    "weights": {
        "component_criticality": 0.40,
        "impact_scope": 0.30,
        "business_rule_sensitivity": 0.30,
    },
    "thresholds": {
        "low": 40,
        "high": 75,
    },
    "scope_cap": 5,
    "source_criticality_weight": 0.60,
}

CRITICALITY_VALUES = {
    "LOW": 1,
    "MEDIUM": 2,
    "HIGH": 3,
}

SENSITIVITY_VALUES = {
    "LOW": 0,
    "MEDIUM": 50,
    "HIGH": 100,
}


class RiskEngine:
    """Calculate explainable business risk using configurable weights."""

    def __init__(self, config=None):
        """Initialize and validate the organization's scoring configuration."""

        self.config = config if config is not None else DEFAULT_CONFIG

        self.weights = self.config["weights"]
        self.thresholds = self.config["thresholds"]
        self.scope_cap = self.config.get("scope_cap", 5)

        self.source_criticality_weight = self.config.get(
            "source_criticality_weight",
            0.60,
        )

        required_factors = {
            "component_criticality",
            "impact_scope",
            "business_rule_sensitivity",
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

        if (
            not isinstance(self.source_criticality_weight, (int, float))
            or isinstance(self.source_criticality_weight, bool)
            or not 0 <= self.source_criticality_weight <= 1
        ):
            raise ValueError(
                "source_criticality_weight must be between 0 and 1"
            )

    def assess(
        self,
        change_id,
        impacts,
        components,
        business_rule_sensitivity,
        critical_business_control=False,
        source_component_id=None,
    ):
        """
        Calculate business risk for a proposed change.

        Args:
            change_id:
                Unique identifier for the proposed change.

            impacts:
                Downstream components returned by DependencyAnalyzer.

            components:
                Architecture records containing component criticality.

            business_rule_sensitivity:
                Documented sensitivity: LOW, MEDIUM, or HIGH.

            critical_business_control:
                Whether documented evidence identifies a critical
                business control affected by the change.

            source_component_id:
                Identifier of the component being modified.

                Optional temporarily for compatibility with existing
                tests and callers. New assessments should provide it.

        Returns:
            Explainable deterministic risk assessment.
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

        # Count each downstream component once.
        impacted_ids = sorted({
            impact["component_id"]
            for impact in impacts
        })

        if source_component_id is not None:

            if source_component_id not in component_map:
                raise ValueError(
                    f"Unknown source component: {source_component_id}"
                )

            if source_component_id in impacted_ids:
                raise ValueError(
                    "Source component cannot be a downstream impact"
                )

        def normalized_criticality(component_id):
            """Convert documented component criticality to a 0-100 score."""

            if component_id not in component_map:
                raise ValueError(
                    f"Unknown impacted component: {component_id}"
                )

            criticality = component_map[component_id]["criticality"]

            if criticality not in CRITICALITY_VALUES:
                raise ValueError(
                    f"Invalid criticality for {component_id}"
                )

            return (
                (CRITICALITY_VALUES[criticality] - 1) / 2
            ) * 100

        # Evaluate downstream criticality.
        # Use maximum downstream criticality to prevent dilution.
        downstream_values = [
            normalized_criticality(component_id)
            for component_id in impacted_ids
        ]

        downstream_score = max(downstream_values, default=0)

        # Evaluate source criticality.
        if source_component_id is not None:
            source_score = normalized_criticality(
                source_component_id
            )
        else:
            source_score = None

        # Combine source and downstream criticality.
        if source_score is None:

            # Temporary compatibility with downstream-only callers.
            criticality_score = downstream_score

        elif not downstream_values:

            # No documented downstream impact must not dilute
            # the source component's criticality.
            criticality_score = source_score

        else:
            # Source establishes the baseline.
            # Downstream exposure can increase, never reduce it.
            downstream_contribution_weight = (
                1 - self.source_criticality_weight
            )

            criticality_score = source_score + (
                (100 - source_score)
                * (downstream_score / 100)
                * downstream_contribution_weight
            )

        # Scope counts downstream components only.
        scope_score = min(
            len(impacted_ids) / self.scope_cap,
            1,
        ) * 100

        sensitivity_score = SENSITIVITY_VALUES[
            business_rule_sensitivity
        ]

        factor_scores = {
            "component_criticality": round(criticality_score, 2),
            "impact_scope": round(scope_score, 2),
            "business_rule_sensitivity": sensitivity_score,
        }

        weighted_score = round(
            sum(
                factor_scores[factor] * self.weights[factor]
                for factor in factor_scores
            ),
            2,
        )

        if weighted_score >= self.thresholds["high"]:
            weighted_level = "HIGH"

        elif weighted_score >= self.thresholds["low"]:
            weighted_level = "MEDIUM"

        else:
            weighted_level = "LOW"

        # Documented critical business controls establish a HIGH floor.
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
            f"Business rule sensitivity: {business_rule_sensitivity}",
        ]

        if source_component_id is not None:
            reasons.append(
                f"Changed source component: {source_component_id}"
            )

            if not impacted_ids:
                reasons.append(
                    "No documented downstream impacts; architecture "
                    "completeness must be assessed separately"
                )

        if critical_business_control:
            reasons.append(
                "Documented critical business control: minimum HIGH risk"
            )

        return {
            "change_id": change_id,
            "source_component_id": source_component_id,
            "weighted_score": weighted_score,
            "weighted_level": weighted_level,
            "risk_level": final_level,
            "guardrail_applied": guardrail_applied,
            "impacted_component_count": len(impacted_ids),
            "factor_scores": factor_scores,
            "source_criticality_score": (
                round(source_score, 2)
                if source_score is not None
                else None
            ),
            "downstream_criticality_score": round(
                downstream_score,
                2,
            ),
            "source_criticality_weight": (
                self.source_criticality_weight
            ),
            "weights": dict(self.weights),
            "reasons": reasons,
        }