"""Retrieve PIVOT architecture datasets from local JSON files.

This repository handles data retrieval and JSON decoding.

It does not determine whether architecture records are structurally
valid or whether their supporting evidence is trustworthy.

Those responsibilities belong to DataValidator.
"""

import json
from pathlib import Path
from typing import Any


class ArchitectureDataUnavailableError(Exception):
    """Raised when required architecture data cannot be retrieved."""


class ArchitectureRepository:
    """Retrieve architecture datasets independently of assessment logic."""

    def __init__(self, data_directory: str | Path) -> None:
        """Initialize the repository with a local data directory."""
        self.data_directory = Path(data_directory)

    def load(self, filename: str) -> Any:
        """Retrieve and decode a JSON dataset.

        Args:
            filename: Name of the JSON file to retrieve.

        Returns:
            Parsed JSON data, including valid empty datasets.

        Raises:
            ValueError: If the filename is invalid.
            ArchitectureDataUnavailableError: If the file cannot be
                read or contains malformed JSON.
        """
        if (
            not filename
            or Path(filename).name != filename
            or not filename.endswith(".json")
        ):
            raise ValueError("filename must be a simple .json filename")

        path = self.data_directory / filename

        try:
            with path.open("r", encoding="utf-8") as stream:
                return json.load(stream)

        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ArchitectureDataUnavailableError(
                f"Required architecture data unavailable: {filename}"
            ) from exc

    def load_components(self) -> Any:
        """Retrieve component records without validating them."""
        return self.load("components.json")

    def load_dependencies(self) -> Any:
        """Retrieve dependency records, including an empty list."""
        return self.load("dependencies.json")

    def load_business_rules(self) -> Any:
        """Retrieve business-rule records without validating them."""
        return self.load("business_rules.json")
