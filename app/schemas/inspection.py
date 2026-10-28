
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


InspectionOutcome = Literal[
    "ISSUE_IDENTIFIED",
    "NO_ISSUE_FOUND",
    "FURTHER_TESTING_REQUIRED",
    "REPAIR_REQUIRED",
]


class InspectionCreate(BaseModel):
    """Validate the data submitted when recording an inspection."""

    complaint_number: str = Field(
        min_length=1,
        max_length=50,
        description="Complaint number being inspected",
    )

    inspected_by: str = Field(
        min_length=1,
        max_length=150,
        description="Name of the person inspecting the machine",
    )

    inspection_findings: str = Field(
        min_length=3,
        max_length=10000,
        description="Findings observed during physical inspection",
    )

    issue_type_id: int | None = Field(
        default=None,
        ge=1,
        description="Issue identified during inspection, if known",
    )

    inspection_outcome: InspectionOutcome

    recommended_action: str | None = Field(
        default=None,
        max_length=5000,
        description="Recommended next action",
    )

    inspection_notes: str | None = Field(
        default=None,
        max_length=10000,
        description="Additional inspection notes",
    )

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )
