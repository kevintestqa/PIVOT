"""
PIVOT - Architecture Data Validator

Purpose:
    Validate architecture dependency records before impact analysis.

Responsibilities:
    - Identify invalid component references.
    - Detect duplicate dependency relationships.
    - Evaluate verification evidence freshness.
    - Identify missing or malformed verification dates.
    - Preserve valid records when invalid records are encountered.
    - Provide explainable validation findings.

Business Rules:
    - Default verification threshold: 90 days.
    - Dependencies verified exactly 90 days ago remain current.
    - Dependencies older than 90 days are STALE.
    - Missing verification dates are UNVERIFIED.
    - Future verification dates are INVALID.

Limitations:
    - Data validation does not determine business risk.
    - Stale documentation does not prove a dependency is incorrect.
    - The assessment workflow determines whether incomplete
      architecture evidence is sufficient for analysis.
"""

from datetime import date


class DataValidator:
    """Validate architecture dependency records."""

    def __init__(self, components, dependencies, threshold_days=90):
        if threshold_days < 0:
            raise ValueError("Threshold cannot be negative")

        self.components = components
        self.dependencies = dependencies
        self.threshold_days = threshold_days

    def validate(self, assessment_date=None):
        """Validate dependencies and return explainable findings."""

        assessment_date = assessment_date or date.today()

        if isinstance(assessment_date, str):
            assessment_date = date.fromisoformat(assessment_date)

        component_ids = {component["id"] for component in self.components}

        valid_records = []
        invalid_records = []
        duplicates = []
        stale_records = []
        unverified_records = []

        seen = {}

        for index, dependency in enumerate(self.dependencies):
            record_id = dependency.get("id", f"RECORD-{index}")
            source = dependency.get("source")
            target = dependency.get("target")

            errors = []

            if source not in component_ids:
                errors.append(f"Unknown source: {source}")

            if target not in component_ids:
                errors.append(f"Unknown target: {target}")

            last_verified = dependency.get("last_verified")
            verified_date = None

            if last_verified:
                try:
                    verified_date = date.fromisoformat(last_verified)

                    if verified_date > assessment_date:
                        errors.append("Verification date is in the future")

                except (ValueError, TypeError):
                    errors.append("Invalid verification date")

            # Reject the record only after completing validation.
            if errors:
                invalid_records.append(
                    {
                        "record_id": record_id,
                        "source": source,
                        "target": target,
                        "errors": errors,
                        "reason": "; ".join(errors),
                    }
                )
                continue

            valid_records.append(dependency)

            # Detect duplicate relationships.
            key = (
                source,
                target,
                dependency.get("relationship"),
            )

            if key in seen:
                duplicates.append(
                    {
                        "record_id": record_id,
                        "duplicate_of": seen[key],
                    }
                )
            else:
                seen[key] = record_id

            # Classify verification freshness.
            if verified_date is None:
                unverified_records.append(
                    {
                        "record_id": record_id,
                        "source": source,
                        "target": target,
                        "reason": "No verification date was provided",
                    }
                )
            else:
                age = (assessment_date - verified_date).days

                if age > self.threshold_days:
                    stale_records.append(
                        {
                            "record_id": record_id,
                            "source": source,
                            "target": target,
                            "age_days": age,
                            "reason": (
                                f"Verification is {age} days old, exceeding "
                                f"the {self.threshold_days}-day threshold"
                            ),
                        }
                    )

        return {
            "total_records": len(self.dependencies),
            "valid_records": valid_records,
            "invalid_records": invalid_records,
            "duplicates": duplicates,
            "stale_records": stale_records,
            "unverified_records": unverified_records,
        }