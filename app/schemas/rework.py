
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ReworkCreate(BaseModel):
    complaint_number: str = Field(min_length=1, max_length=50)
    performed_by: str = Field(min_length=2, max_length=150)
    rework_action: str = Field(min_length=3, max_length=5000)
    parts_replaced: str | None = Field(default=None, max_length=5000)

    rework_result: Literal[
        "COMPLETED",
        "UNSUCCESSFUL",
        "PARTIALLY_COMPLETED",
    ]

    requires_testing: bool = True
    rework_notes: str | None = Field(default=None, max_length=5000)

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )
