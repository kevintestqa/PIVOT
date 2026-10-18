from datetime import date


class DataValidator:
    """
    Validates architecture dependency records.

    Detects invalid records, duplicates, and stale evidence.
    """

    def __init__(self, components, dependencies, threshold_days=90):
        self.components = components
        self.dependencies = dependencies
        self.threshold_days = threshold_days

    def validate(self, assessment_date=None):
        assessment_date = assessment_date or date.today()

        component_ids = {
            component["id"] for component in self.components
        }

        valid_records = []
        invalid_records = []
        duplicates = []
        stale_records = []

        seen = {}

        for dependency in self.dependencies:
            record_id = dependency.get("id", "UNKNOWN")
            source = dependency.get("source")
            target = dependency.get("target")

            errors = []

            if source not in component_ids:
                errors.append(f"Unknown source: {source}")

            if target not in component_ids:
                errors.append(f"Unknown target: {target}")

            if errors:
                invalid_records.append({
                    "record_id": record_id,
                    "errors": errors
                })
                continue

            valid_records.append(dependency)

            relationship = dependency.get("relationship")
            key = (source, target, relationship)

            if key in seen:
                duplicates.append({
                    "record_id": record_id,
                    "duplicate_of": seen[key]
                })
            else:
                seen[key] = record_id

            last_verified = dependency.get("last_verified")

            if last_verified:
                try:
                    verified_date = date.fromisoformat(last_verified)
                    age = (assessment_date - verified_date).days

                    if age > self.threshold_days:
                        stale_records.append({
                            "record_id": record_id,
                            "age_days": age
                        })

                except (ValueError, TypeError):
                    invalid_records.append({
                        "record_id": record_id,
                        "errors": ["Invalid verification date"]
                    })
                    valid_records.pop()

        return {
            "total_records": len(self.dependencies),
            "valid_records": valid_records,
            "invalid_records": invalid_records,
            "duplicates": duplicates,
            "stale_records": stale_records
        }