"""Domain dataclasses."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ValidationReport:
    missing_possible_values: list[str] = field(default_factory=list)
    classes_without_description: list[str] = field(default_factory=list)
    class_properties_without_values: list[tuple[str, str]] = field(default_factory=list)
    properties_not_used: list[str] = field(default_factory=list)
    class_ranges_out_of_possible_bounds: list[tuple[str, str, float | None, float | None, float | None, float | None]] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not any([
            self.missing_possible_values,
            self.classes_without_description,
            self.class_properties_without_values,
            self.class_ranges_out_of_possible_bounds,
        ])


@dataclass
class RejectionReason:
    class_name: str
    property_name: str
    input_value: float
    range_min: Optional[float] = None
    range_max: Optional[float] = None
    message: Optional[str] = None


@dataclass
class ClassificationResult:
    final_class: Optional[str]
    matched_classes: list[str]
    rejected: list[RejectionReason]
    source: str
    matching_rows: list[tuple[str, str]] = field(default_factory=list)
    probabilities: list[tuple[str, float]] = field(default_factory=list)
    note: str = ''
    evaluated_properties: list[str] = field(default_factory=list)
    ml_note: str = ''
