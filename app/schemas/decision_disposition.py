
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class DecisionCreate(BaseModel):
    complaint_number: str = Field(min_length=1, max_length=50)
    decision_type: Literal["ACCEPTED", "REJECTED"]
    decision_reason: str = Field(min_length=3, max_length=5000)
    rejection_reason: str | None = Field(default=None, max_length=5000)
    decided_by: str = Field(min_length=2, max_length=150)

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    @model_validator(mode="after")
    def validate_rejection_reason(self):
        if self.decision_type == "REJECTED":
            if not self.rejection_reason or len(self.rejection_reason.strip()) < 3:
                raise ValueError(
                    "A rejection reason of at least 3 characters is required."
                )

        return self


class DispositionCreate(BaseModel):
    complaint_number: str = Field(min_length=1, max_length=50)

    disposition_type: Literal[
        "RETURN_TO_STOCK",
        "SCRAP",
        "HOLD",
        "RETURN_TO_DEALER",
        "OTHER",
    ]

    disposition_reason: str = Field(min_length=3, max_length=5000)
    recorded_by: str = Field(min_length=2, max_length=150)

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )
