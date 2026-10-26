"""Coordinate PIVOT assessments without owning data retrieval or scoring.

Increment 1 checks that required datasets can be retrieved. Validation,
impact analysis, and risk scoring will be integrated in later increments.
"""

from src.architecture_repository import ArchitectureDataUnavailableError


class AssessmentEngine:
    """Translate repository retrieval outcomes into assessment workflow states."""

    def __init__(self, repository, validator=None):
        """Accept a repository and an optional validator dependency."""
        self.repository = repository
        self.validator = validator

    def assess(self, change_id, source_component_id):
        """Retrieve required datasets and report readiness for validation."""
        result = {
            "change_id": change_id,
            "source_component_id": source_component_id,
            "assessment_state": "READY_FOR_VALIDATION",
            "risk_level": None,
            "weighted_score": None,
            "reason": None,
        }

        try:
            components = self.repository.load_components()
            dependencies = self.repository.load_dependencies()
            business_rules = self.repository.load_business_rules()
        except ArchitectureDataUnavailableError as exc:
            result["assessment_state"] = "UNAVAILABLE"
            result["reason"] = str(exc)
            return result

        # Retrieval succeeded; validation and risk scoring come later.
        result["retrieved_record_counts"] = {
            "components": len(components),
            "dependencies": len(dependencies),
            "business_rules": len(business_rules),
        }

        # Execute validation when a validator is provided.
        if self.validator is not None:
            validator = self.validator(components, dependencies)
            result["validation_results"] = validator.validate()

        return result