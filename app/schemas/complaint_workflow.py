
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


ComplaintStatus = Literal[
    "REGISTERED",
    "UNDER_INSPECTION",
    "ASSIGNED",
    "UNDER_REWORK",
    "UNDER_TESTING",
    "AWAITING_DECISION",
    "AWAITING_DISPOSITION",
    "AWAITING_DISPATCH",
    "CLOSED",
]


class ComplaintStatusUpdate(BaseModel):
    """Validate a requested complaint status change."""

    new_status: ComplaintStatus

    changed_by: str = Field(
        min_length=1,
        max_length=150,
    )

    reason: str = Field(
        min_length=3,
        max_length=2000,
    )

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )
