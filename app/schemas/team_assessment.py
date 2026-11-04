
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class TeamAssessmentCreate(BaseModel):
    complaint_number: str = Field(min_length=1, max_length=50)

    assessed_by: str = Field(min_length=2, max_length=150)

    assessment_findings: str = Field(
        min_length=3,
        max_length=10000,
    )

    recommended_action: str = Field(
        min_length=3,
        max_length=5000,
    )

    assessment_outcome: Literal[
        "REPAIR_REQUIRED",
        "NO_REPAIR_REQUIRED",
        "FURTHER_INVESTIGATION_REQUIRED",
    ]

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )
